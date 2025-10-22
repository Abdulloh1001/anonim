import os
import hmac
import hashlib
from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters,
)
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHANNEL_LINK = os.getenv("CHANNEL_LINK", "https://t.me/eclipse_1oo1")
SECRET_KEY = os.getenv("SECRET_KEY", "anon123")

# Foydalanuvchilar o‘rtasidagi anonim sessiyalar
SESSIONS = {}  # anon_id -> owner_id
REPLY_MAP = {}  # owner_message_id -> anon_id

ALPH = "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"


def b62encode(n: int) -> str:
    if n == 0:
        return ALPH[0]
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

        if owner_id == user.id:
            await update.message.reply_text("🪞 Siz o‘zingizning havolangizni bosdingiz.\nEndi anonim xabar yuborishingiz mumkin!")
            return

        if owner_id:
            SESSIONS[user.id] = owner_id
            await update.message.reply_text("🔒 Endi anonim xabar yuborishingiz mumkin!")
            return

    # Foydalanuvchi o‘z havolasini oladi
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
    target_id = SESSIONS.get(user.id)

    # Agar reply orqali yozilgan bo‘lsa
    if msg.reply_to_message and msg.reply_to_message.message_id in REPLY_MAP:
        anon_id = REPLY_MAP[msg.reply_to_message.message_id]
        await context.bot.send_message(chat_id=anon_id, text=f"🕶 Egasidan javob:\n{msg.text}")
        await msg.reply_text("✅ Javob anonim foydalanuvchiga yuborildi.")
        return

    # Anonim foydalanuvchi yozsa
    if target_id:
        sent = await context.bot.send_message(
            chat_id=target_id,
            text=f"🕶 <b>Anonimdan:</b>\n{msg.text}",
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("💬 Javob yozish", callback_data=f"reply_{user.id}")]
            ])
        )
        REPLY_MAP[sent.message_id] = user.id
        await msg.reply_text("✅ Xabaringiz anonim tarzda yuborildi.")
        return

    await msg.reply_text("❗ Avval /start buyrug‘i orqali anonim suhbatni boshlang.")


async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user = query.from_user

    if query.data.startswith("reply_"):
        anon_id = int(query.data.split("_")[1])
        SESSIONS[user.id] = anon_id
        await query.message.reply_text("✍️ Endi javob yozishingiz mumkin — yozgan xabaringiz anonim tarzda yuboriladi.")


def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(handle_callback))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("🤖 Bot ishga tushdi...")
    app.run_polling()


if __name__ == "__main__":
    main()
