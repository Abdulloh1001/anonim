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

# Foydalanuvchilar o‘rtasidagi anonim bog‘lanish
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
    args = context.args

    if args and args[0]:
        owner_id = parse_payload(args[0])
        if owner_id and owner_id != user.id:
            SESSIONS[user.id] = owner_id
            SESSIONS[owner_id] = user.id
            await update.message.reply_text(
                "🔒 Endi anonim xabar yuborishingiz mumkin!"
            )
            return

    # foydalanuvchi o‘z havolasini oladi
    payload = make_payload(user.id)
    link = f"https://t.me/{context.bot.username}?start={payload}"

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("📢 Kanalga o'tish", url=CHANNEL_LINK)]
    ])

    await update.message.reply_text(
        f"<b>🔒 Sizning maxsus havolangiz:</b>\n{link}\n\n"
        "Bu havola orqali boshqa foydalanuvchilar sizga anonim xabar yuborishi mumkin.\n\n"
        "📢 Yangiliklardan xabardor bo‘lish uchun kanalimizga qo‘shiling 👇",
        parse_mode="HTML",
        reply_markup=keyboard
    )


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message
    user = update.effective_user
    target_id = None

    # Reply orqali yozgan bo‘lsa
    if msg.reply_to_message:
        replied_from = msg.reply_to_message.from_user.id
        # agar bu bot bo‘lsa, reply kimga tegishli ekanini aniqlaymiz
        for k, v in SESSIONS.items():
            if v == user.id and k != user.id:
                target_id = k
                break
    else:
        target_id = SESSIONS.get(user.id)

    if not target_id:
        await msg.reply_text("❗ /start buyrug‘i orqali anonim suhbatni boshlang.")
        return

    try:
        if msg.text:
            await context.bot.send_message(
                chat_id=target_id,
                text=f"🕶 <b>Anonimdan xabar:</b>\n{msg.text}",
                parse_mode="HTML"
            )
        elif msg.photo:
            file_id = msg.photo[-1].file_id
            await context.bot.send_photo(chat_id=target_id, photo=file_id, caption="🕶 Anonimdan rasm")
        elif msg.video:
            file_id = msg.video.file_id
            await context.bot.send_video(chat_id=target_id, video=file_id, caption="🕶 Anonimdan video")
        elif msg.voice:
            file_id = msg.voice.file_id
            await context.bot.send_voice(chat_id=target_id, voice=file_id, caption="🕶 Anonimdan ovozli xabar")
        elif msg.audio:
            file_id = msg.audio.file_id
            await context.bot.send_audio(chat_id=target_id, audio=file_id, caption="🕶 Anonimdan audio")

        await msg.reply_text("✅ Xabaringiz anonim tarzda yuborildi.")
    except Exception as e:
        await msg.reply_text(f"❌ Xatolik: {e}")


def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(
        filters.ALL & ~filters.COMMAND,
        handle_message
    ))

    print("🤖 Bot ishga tushdi...")
    app.run_polling()


if __name__ == "__main__":
    main()
