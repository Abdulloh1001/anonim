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
SESSIONS = {}

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
    if args and args[0]:
        owner_id = parse_payload(args[0])
        if owner_id and owner_id != user.id:
            SESSIONS[user.id] = owner_id
            await update.message.reply_text(
                "🔒 Anonim xabar yuborish uchun xabaringizni yozing yoki media yuboring!"
            )
            return

    payload = make_payload(user.id)
    link = f"https://t.me/{context.bot.username}?start={payload}"

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("📢 Kanalga o'tish", url=CHANNEL_LINK)]
    ])

    await update.message.reply_text(
        f"<b>🔒 Sizning maxsus havolangiz:</b>\n{link}\n\n"
        "Bu havola orqali anonim xabarlar yuboriladi.\n\n"
        "📨 Ular sizga shunday ko‘rinishda yetadi:\n"
        "✍️ Matn xabarlar\n"
        "📸 Rasm / video / audio / ovozli xabarlar\n\n"
        "📢 Yangiliklardan xabardor bo‘lish uchun kanalimizga qo‘shiling 👇",
        parse_mode="HTML",
        reply_markup=keyboard
    )


async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    msg = update.message
    anon_for = SESSIONS.get(user.id)

    if anon_for:
        await context.bot.send_message(
            chat_id=anon_for,
            text=f"🕶 <b>Anonimdan xabar:</b>\n{msg.text}",
            parse_mode="HTML"
        )
        await msg.reply_text("✅ Xabaringiz anonim tarzda yuborildi.")
    else:
        await msg.reply_text("❗ /start buyrug‘i orqali anonim suhbatni boshlang.")


async def handle_media(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    msg = update.message
    anon_for = SESSIONS.get(user.id)

    if not anon_for:
        await msg.reply_text("❗ Siz anonim suhbatni boshlamagansiz.")
        return

    try:
        if msg.photo:
            file_id = msg.photo[-1].file_id
            await context.bot.send_photo(chat_id=anon_for, photo=file_id, caption="🕶 Anonimdan rasm")
        elif msg.video:
            file_id = msg.video.file_id
            await context.bot.send_video(chat_id=anon_for, video=file_id, caption="🕶 Anonimdan video")
        elif msg.voice:
            file_id = msg.voice.file_id
            await context.bot.send_voice(chat_id=anon_for, voice=file_id, caption="🕶 Anonimdan ovozli xabar")
        elif msg.audio:
            file_id = msg.audio.file_id
            await context.bot.send_audio(chat_id=anon_for, audio=file_id, caption="🕶 Anonimdan audio")
        await msg.reply_text("✅ Media yuborildi.")
    except Exception as e:
        await msg.reply_text(f"❌ Xatolik: {e}")


def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    app.add_handler(MessageHandler(
        (filters.PHOTO | filters.VIDEO | filters.VOICE | filters.AUDIO) & ~filters.COMMAND,
        handle_media
    ))

    print("🤖 Bot ishga tushdi...")
    app.run_polling()


if __name__ == "__main__":
    main()
