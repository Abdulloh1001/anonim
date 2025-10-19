from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
import time
from core.utils import (
    ensure_user, make_payload, parse_payload, add_referral,
    record_session, add_tokens, get_tokens, get_referrals,
    display_for, log_channel_send, db_conn
)
from core.config import REF_REWARD, PHOTO_TOKEN_THRESHOLD

ADMIN_IDS = [7404099386]  # Admin ID'larini shu yerga qo'shing

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    is_new = ensure_user(user)
    args = context.args

    # Agar referal orqali kelsa
    if args:
        payload = args[0]
        owner_id = parse_payload(payload)
        if owner_id and owner_id != user.id:
            created = add_referral(owner_id, user.id)
            if created:
                record_session(owner_id, user.id)
                await context.bot.send_message(
                    chat_id=owner_id,
                    text=f"🎉 Sizning referalingiz orqali yangi foydalanuvchi keldi!",
                    parse_mode="Markdown"
                )
                
                prev, new = add_tokens(owner_id, REF_REWARD)
                await log_channel_send(context.bot, f"{display_for(owner_id)} {REF_REWARD} token oldi ✅")

    # Oddiy /start
    pl = make_payload(user.id)
    link = f"https://t.me/{context.bot.username}?start={pl}"

    txt = (
        f"<b>Assalamu alaykum, {user.first_name or 'foydalanuvchi'}!</b>\n\n"
        f"Bu sizning anonim havolangiz:\n<a href='{link}'>{link}</a>\n\n"
        f"Ushbu linkni boshqalarga yuboring — ular sizga anonim xabar yubora oladi.\n\n"
        f"💎 Token yig'ish uchun /token buyrug'ini bosing."
    )

    if is_new:
        txt = "🎉 Profilingiz yaratildi!\n\n" + txt

    await update.message.reply_text(txt, parse_mode="HTML")
    await log_channel_send(context.bot, f"{display_for(user.id)} botni ishga tushirdi (/start)")

async def token(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    ensure_user(user)
    pl = make_payload(user.id)
    link = f"https://t.me/{context.bot.username}?start={pl}"
    
    txt = (
        "🎯 Token yig'ish uchun quyidagi havolani do'stlaringizga yuboring:\n\n"
        f"<a href='{link}'>{link}</a>\n\n"
        "💎 Har bir yangi a'zo uchun 5 ta token olasiz!\n"
        "📱 Premium xususiyatlarni yoqish uchun /balans buyrug'ini bosing."
    )
    
    await update.message.reply_text(txt, parse_mode="HTML")

async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    commands = [
        "/start - Anonim linkni olish",
        "/token - token ishlash",
        "/balans - Tokenlar va referallar",
        "/help - Yordam"
    ]
    
    if user.id in ADMIN_IDS:
        commands.append("/give_tokens <user_id> <amount> - Token hadya qilish")
    
    await update.message.reply_text("📖 Buyruqlar:\n" + "\n".join(commands))

async def balans(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    ensure_user(user)
    tokens = get_tokens(user.id)
    refs = get_referrals(user.id)

    # referallar soni
    ref_count = len(refs) if refs else 0
    ref_text = f"{ref_count} ta odam" if ref_count > 0 else "Hech kim hali"

    conn = db_conn(); c = conn.cursor()
    c.execute("SELECT photo_active FROM users WHERE id=?", (user.id,))
    is_photo_active = c.fetchone()[0]
    conn.close()

    status = (
        "🏅 Premium ta'rif faol!\n\n"
        "Siz yubora oladigan media turlar:\n"
        "🎥 Videolar\n"
        "🎵 Audio/MP3\n"
        "🎤 Ovozli xabarlar"
        if is_photo_active
        else f"🔒 Premium ta'rif uchun {PHOTO_TOKEN_THRESHOLD} token kerak!\n\n"
        "Premium ta'rif orqali yubora oladigan media turlar:\n"
        "🎥 Videolar\n"
        "🎵 Audio/MP3\n"
        "🎤 Ovozli xabarlar"
    )

    keyboard = None
    if not is_photo_active and tokens >= PHOTO_TOKEN_THRESHOLD:
        keyboard = InlineKeyboardMarkup(
            [[InlineKeyboardButton("⚡ Ta'rifni faollashtirish", callback_data="activate_photo")]]
        )

    await update.message.reply_text(
        f"💰 Tokenlaringiz: <b>{tokens}</b>\n"
        f"👥 Taklif qilganlar: {ref_text}\n\n"
        f"💎 Token yig'ish uchun /token buyrug'ini bosing\n\n"
        f"{status}",
        parse_mode="HTML",
        reply_markup=keyboard
    )

async def give_tokens(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if user.id not in ADMIN_IDS:
        return
    
    if len(context.args) != 2:
        await update.message.reply_text("❌ Xato format. Namuna: /give_tokens <user_id> <amount>")
        return
    
    try:
        target_id = int(context.args[0])
        amount = int(context.args[1])
    except ValueError:
        await update.message.reply_text("❌ user_id va amount son bo'lishi kerak")
        return
        
    if amount <= 0:
        await update.message.reply_text("❌ Token miqdori musbat son bo'lishi kerak")
        return
    
    conn = db_conn(); c = conn.cursor()
    c.execute("SELECT id FROM users WHERE id=?", (target_id,))
    if not c.fetchone():
        conn.close()
        await update.message.reply_text("❌ Bunday foydalanuvchi topilmadi")
        return
        
    prev, new = add_tokens(target_id, amount)
    await update.message.reply_text(f"✅ {target_id} ga {amount} token berildi\nYangi balans: {new}")
    await context.bot.send_message(
        chat_id=target_id,
        text=f"🎁 Admin tomonidan sizga {amount} token hadya qilindi!\nYangi balansingiz: {new}"
    )
    await log_channel_send(context.bot, f"👨‍💼 Admin {display_for(user.id)} → {display_for(target_id)}: +{amount} token")
    conn.close()
