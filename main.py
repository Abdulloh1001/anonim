import os
import hmac
import hashlib
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHANNEL_LINK = os.getenv("CHANNEL_LINK", "https://t.me/eclipse_1oo1")
SECRET_KEY = os.getenv("SECRET_KEY", "anon123")

USERS = {}
SESSIONS = {}  # foydalanuvchi id yoki msg_id orqali mapping
ALPH = "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"


def b62encode(n: int) -> str:
    if n == 0: return ALPH[0]
    s = []
    while n > 0:
        s.append(ALPH[n % 62])
        n //= 62
    return ''.join(reversed(s))


def make_payload(user_id: int) -> str:
    uid_part = b62encode(user_id)
    hm = hmac.new(SECRET_KEY.encode(), str(user_id).encode(), hashlib.sha256).digest()
    short = int.from_bytes(hm[:6], 'big')
    return uid_part + b62encode(short)


def parse_payload(payload: str):
    for i in range(1, len(payload)):
        pref = payload[:i]
        rest = payload[i:]
        try:
            uid = 0
            for ch in pref:
                uid = uid * 62 + ALPH.index(ch)
        except ValueError:
            continue
        hm = hmac.new(SECRET_KEY.encode(), str(uid).encode(), hashlib.sha256).digest()
        short = int.from_bytes(hm[:6], 'big')
        if rest == b62encode(short):
            return uid
    return None


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    USERS[user.id] = {"username": user.username}
    args = context.args

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("📢 Kanalimiz", url=CHANNEL_LINK)]
    ])

    # Agar foydalanuvchi boshqa birovning linkidan kirgan bo‘lsa
    if args and args[0]:
        owner_id = parse_payload(args[0])
        if owner_id and owner_id != user.id:
            SESSIONS[user.id] = owner_id
            await update.message.reply_text(
                "🔒 Endi anonim xabar yuborishingiz mumkin!",
                reply_markup=keyboard
            )
            return

    # O'zining maxsus havolasi
    payload = make_payload(user.id)
    link = f"https://t.me/{context.bot.username}?start={payload}"

    await update.message.reply_text(
        f"<b>🔗 Sizning anonim havolangiz:</b>\n{link}\n\n"
        "Bu havolani do‘stlaringizga yuboring, ular sizga anonim xabar yoza olishadi 😎",
        parse_mode="HTML",
        reply_markup=keyboard
    )


async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    msg = update.message
    anon_for = SESSIONS.get(user.id)

    if anon_for:  # anonim xabar
        sent = await context.bot.send_message(
            chat_id=anon_for,
            text=f"🕶 <b>Anonimdan xabar:</b>\n{msg.text}",
            parse_mode="HTML"
        )
        # reply uchun mapping
        SESSIONS[sent.message_id] = user.id
        await msg.reply_text("✅ Xabaringiz anonim tarzda yuborildi.")

    elif msg.reply_to_message and msg.reply_to_message.message_id in SESSIONS:
        target_id = SESSIONS[msg.reply_to_message.message_id]
        sent = await context.bot.send_message(
            chat_id=target_id,
            text=f"💬 <b>Anonimdan javob:</b>\n{msg.text}",
            parse_mode="HTML"
        )
        SESSIONS[sent.message_id] = user.id
        await msg.reply_text("✅ Javob anonim tarzda yuborildi.")
    else:
        await msg.reply_text("❗ /start buyrug‘idan foydalaning yoki havoladan kiring.")


async def handle_media(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    msg = update.message
    anon_for = SESSIONS.get(user.id)

    # 1️⃣ Agar foydalanuvchi kimdadir anonimga yozayotgan bo‘lsa
    if anon_for:
        try:
            caption = "🕶 Anonimdan media"
            sent = None
            if msg.photo:
                sent = await context.bot.send_photo(chat_id=anon_for, photo=msg.photo[-1].file_id, caption=caption)
            elif msg.video:
                sent = await context.bot.send_video(chat_id=anon_for, video=msg.video.file_id, caption=caption)
            elif msg.voice:
                sent = await context.bot.send_voice(chat_id=anon_for, voice=msg.voice.file_id, caption=caption)
            elif msg.audio:
                sent = await context.bot.send_audio(chat_id=anon_for, audio=msg.audio.file_id, caption=caption)
            elif msg.sticker:
                sent = await context.bot.send_sticker(chat_id=anon_for, sticker=msg.sticker.file_id)
            if sent:
                SESSIONS[sent.message_id] = user.id
            await msg.reply_text("✅ Media yuborildi.")
        except Exception as e:
            await msg.reply_text(f"❌ Xatolik: {e}")

    # 2️⃣ Agar reply orqali anonimga javob beryapti
    elif msg.reply_to_message and msg.reply_to_message.message_id in SESSIONS:
        target_id = SESSIONS[msg.reply_to_message.message_id]
        sent = None
        if msg.photo:
            sent = await context.bot.send_photo(chat_id=target_id, photo=msg.photo[-1].file_id, caption="💬 Anonimdan javob:")
        elif msg.video:
            sent = await context.bot.send_video(chat_id=target_id, video=msg.video.file_id, caption="💬 Anonimdan javob:")
        elif msg.voice:
            sent = await context.bot.send_voice(chat_id=target_id, voice=msg.voice.file_id, caption="💬 Anonimdan javob:")
        elif msg.audio:
            sent = await context.bot.send_audio(chat_id=target_id, audio=msg.audio.file_id, caption="💬 Anonimdan javob:")
        elif msg.sticker:
            sent = await context.bot.send_sticker(chat_id=target_id, sticker=msg.sticker.file_id)
        if sent:
            SESSIONS[sent.message_id] = user.id
        await msg.reply_text("✅ Javob anonim tarzda yuborildi.")
    else:
        await msg.reply_text("❗ /start buyrug‘idan foydalaning yoki havoladan kiring.")


def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    app.add_handler(MessageHandler(
        (filters.PHOTO | filters.VIDEO | filters.VOICE | filters.AUDIO | filters.Sticker.ALL) & ~filters.COMMAND,
        handle_media
    ))
    print("🤖 Bot ishga tushdi...")
    app.run_polling()


if __name__ == "__main__":
    main()
