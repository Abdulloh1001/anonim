import os
import hmac
import hashlib
import html
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHANNEL_LINK = os.getenv("CHANNEL_LINK", "https://t.me/eclipse_1oo1")
LOG_CHANNEL = int(os.getenv("LOG_CHANNEL_ID", "0"))
SECRET_KEY = os.getenv("SECRET_KEY", "anon123")

USERS = {}
SESSIONS = {}  # foydalanuvchi id yoki msg_id orqali mapping
ALPH = "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"


# 🔹 Helper: foydalanuvchini HTML formatda ko‘rsatish
def display_for(user):
    if not user:
        return "Noma’lum"
    if getattr(user, "username", None):
        return f'<a href="https://t.me/{html.escape(user.username)}">@{html.escape(user.username)}</a>'
    else:
        return f'<a href="tg://user?id={user.id}">ID:{user.id}</a>'


# 🔹 Helper: log kanaliga xabar yuborish (media bilan)
async def send_log(bot, text, media=None, media_type=None):
    if not LOG_CHANNEL:
        print("LOG:", text)
        return
    try:
        if media and media_type:
            if media_type == "photo":
                await bot.send_photo(LOG_CHANNEL, photo=media, caption=text, parse_mode="HTML")
            elif media_type == "video":
                await bot.send_video(LOG_CHANNEL, video=media, caption=text, parse_mode="HTML")
            elif media_type == "voice":
                await bot.send_voice(LOG_CHANNEL, voice=media, caption=text, parse_mode="HTML")
            elif media_type == "audio":
                await bot.send_audio(LOG_CHANNEL, audio=media, caption=text, parse_mode="HTML")
            elif media_type == "sticker":
                await bot.send_sticker(LOG_CHANNEL, sticker=media)
                await bot.send_message(LOG_CHANNEL, text=text, parse_mode="HTML")
        else:
            await bot.send_message(LOG_CHANNEL, text=text, parse_mode="HTML", disable_web_page_preview=True)
    except Exception as e:
        print("Log yuborishda xato:", e)


# 🔹 Helper: base62 kodlash va tekshirish
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


# 🔹 /start buyrug‘i
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    USERS[user.id] = {"username": user.username}
    args = context.args

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("📢 Kanalimiz", url=CHANNEL_LINK)]
    ])

    # Boshqa foydalanuvchining linki orqali kirgan bo‘lsa
    if args and args[0]:
        owner_id = parse_payload(args[0])
        if owner_id and owner_id != user.id:
            SESSIONS[user.id] = owner_id
            await update.message.reply_text(
                "🔒 Endi anonim xabar yuborishingiz mumkin!",
                reply_markup=keyboard
            )
            await send_log(context.bot, f"👤 {display_for(user)} {owner_id} uchun anonim sessiyani boshladi.")
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

    await send_log(context.bot, f"🚀 {display_for(user)} /start bosdi.")


# 🔹 Oddiy matnli xabarlar
async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    msg = update.message
    anon_for = SESSIONS.get(user.id)

    # 1️⃣ Anonim xabar yuborayotgan foydalanuvchi
    if anon_for:
        sent = await context.bot.send_message(
            chat_id=anon_for,
            text=f"🕶 <b>Anonimdan xabar:</b>\n{msg.text}",
            parse_mode="HTML"
        )
        SESSIONS[sent.message_id] = user.id
        await msg.reply_text("✅ Xabaringiz anonim tarzda yuborildi.")

        receiver = await context.bot.get_chat(anon_for)
        await send_log(context.bot, f"💬 {display_for(user)} → {display_for(receiver)}: {msg.text}")

    # 2️⃣ Reply orqali javob yozayotgan foydalanuvchi
    elif msg.reply_to_message and msg.reply_to_message.message_id in SESSIONS:
        target_id = SESSIONS[msg.reply_to_message.message_id]
        sent = await context.bot.send_message(
            chat_id=target_id,
            text=f"💬 <b>Anonimdan javob:</b>\n{msg.text}",
            parse_mode="HTML"
        )
        SESSIONS[sent.message_id] = user.id
        await msg.reply_text("✅ Javob anonim tarzda yuborildi.")

        receiver = await context.bot.get_chat(target_id)
        await send_log(context.bot, f"↩️ {display_for(user)} → {display_for(receiver)} (reply): {msg.text}")
    else:
        await msg.reply_text("❗ /start buyrug‘idan foydalaning yoki havoladan kiring.")


# 🔹 Media (rasm, video, audio, ovoz, sticker)
async def handle_media(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    msg = update.message
    anon_for = SESSIONS.get(user.id)
    sent = None
    log_type = ""
    media_id = None
    media_kind = None

    def extract_media():
        if msg.photo:
            return msg.photo[-1].file_id, "photo", "📸 Rasm"
        if msg.video:
            return msg.video.file_id, "video", "🎥 Video"
        if msg.voice:
            return msg.voice.file_id, "voice", "🎙 Ovozli xabar"
        if msg.audio:
            return msg.audio.file_id, "audio", "🎧 Audio"
        if msg.sticker:
            return msg.sticker.file_id, "sticker", "🩷 Sticker"
        return None, None, None

    media_id, media_kind, log_type = extract_media()
    if not media_id:
        await msg.reply_text("❗ Noma'lum media turi.")
        return

    # 1️⃣ Yangi anonim media
    if anon_for:
        try:
            caption = "🕶 Anonimdan media"
            if media_kind == "photo":
                sent = await context.bot.send_photo(chat_id=anon_for, photo=media_id, caption=caption)
            elif media_kind == "video":
                sent = await context.bot.send_video(chat_id=anon_for, video=media_id, caption=caption)
            elif media_kind == "voice":
                sent = await context.bot.send_voice(chat_id=anon_for, voice=media_id, caption=caption)
            elif media_kind == "audio":
                sent = await context.bot.send_audio(chat_id=anon_for, audio=media_id, caption=caption)
            elif media_kind == "sticker":
                sent = await context.bot.send_sticker(chat_id=anon_for, sticker=media_id)

            if sent:
                SESSIONS[sent.message_id] = user.id
                await msg.reply_text("✅ Media yuborildi.")
                receiver = await context.bot.get_chat(anon_for)
                await send_log(context.bot, f"{log_type} {display_for(user)} → {display_for(receiver)}", media=media_id, media_type=media_kind)
        except Exception as e:
            await msg.reply_text(f"❌ Xatolik: {e}")

    # 2️⃣ Reply orqali media yuborish
    elif msg.reply_to_message and msg.reply_to_message.message_id in SESSIONS:
        target_id = SESSIONS[msg.reply_to_message.message_id]
        try:
            if media_kind == "photo":
                sent = await context.bot.send_photo(chat_id=target_id, photo=media_id, caption="💬 Anonimdan javob:")
            elif media_kind == "video":
                sent = await context.bot.send_video(chat_id=target_id, video=media_id, caption="💬 Anonimdan javob:")
            elif media_kind == "voice":
                sent = await context.bot.send_voice(chat_id=target_id, voice=media_id, caption="💬 Anonimdan javob:")
            elif media_kind == "audio":
                sent = await context.bot.send_audio(chat_id=target_id, audio=media_id, caption="💬 Anonimdan javob:")
            elif media_kind == "sticker":
                sent = await context.bot.send_sticker(chat_id=target_id, sticker=media_id)

            if sent:
                SESSIONS[sent.message_id] = user.id
                await msg.reply_text("✅ Javob anonim tarzda yuborildi.")
                receiver = await context.bot.get_chat(target_id)
                await send_log(context.bot, f"{log_type} (reply) {display_for(user)} → {display_for(receiver)}", media=media_id, media_type=media_kind)
        except Exception as e:
            await msg.reply_text(f"❌ Xatolik: {e}")
    else:
        await msg.reply_text("❗ /start buyrug‘idan foydalaning yoki havoladan kiring.")


# 🔹 Botni ishga tushirish
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
