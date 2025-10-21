from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
import time
from core.utils import (
    ensure_user, make_payload, parse_payload,
    record_session, display_for, log_channel_send, db_conn
)
from core.config import CHANNEL_LINK

ADMIN_IDS = [7404099386]  # Admin ID'larini shu yerga qo'shing

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    is_new = ensure_user(user)
    args = context.args

    if args and args[0]:  # Agar havoladan kirgan bo'lsa
        start_arg = args[0]
        # ID ni aniqlaymiz
        owner_id = parse_payload(start_arg)
        if owner_id == user.id:
            await update.message.reply_text("❌ O'zingizga xabar yubora olmaysiz!")
            return
            
        if owner_id:
            record_session(owner_id, user.id)
            await update.message.reply_text(
                "🔒 Anonim chatga xush kelibsiz! \n"
                "Endi siz xabaringizni yuboring, men uni egasiga yetkazaman.\n\n"
                "Yuborish mumkin:\n"
                "✍️ Matn xabarlar\n"
                "📸 Rasmlar\n"
                "🎥 Videolar\n"
                "🎵 Audio/MP3\n"
                "🎤 Ovozli xabarlar"
            )
            return

    # Yangi foydalanuvchiga botni tushuntirish
    if is_new:
        await update.message.reply_text(
            "👋 Botga xush kelibsiz!\n\n"
            "Bu bot orqali siz anonim xabarlar yuborishingiz mumkin.\n"
            "/help - qo'llanma olish"
        )
    
    payload = make_payload(user.id)
    link = f"https://t.me/{context.bot.username}?start={payload}"
    
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("📢 Kanalimizga qo'shiling", url=CHANNEL_LINK)]
    ])
    
    await update.message.reply_text(
        f"<b>🔒 Sizning maxsus havolangiz:</b>\n{link}\n\n"
        f"<b>Bu havola orqali do'stlaringiz sizga quyidagilarni yubora olishadi:</b>\n"
        f"✍️ Matn xabarlar\n"
        f"📸 Rasmlar\n"
        f"🎥 Videolar\n"
        f"🎵 Audio/MP3\n"
        f"🎤 Ovozli xabarlar\n\n"
        f"<i>📢 Yangiliklar va e'lonlar uchun kanalimizga qo'shiling</i>",
        parse_mode="HTML",
        reply_markup=keyboard
    ),(
        f"Ushbu linkni boshqalarga yuboring — do'stlaringiz kanal a'zosi bo'lganda siz token olasiz!\n\n"
        f"💎 Token yig'ish uchun /token buyrug'ini bosing."
    )

    if is_new:
        txt = "🎉 Profilingiz yaratildi!\n\n" + txt

    await update.message.reply_text(txt, parse_mode="HTML")
    await log_channel_send(context.bot, f"{display_for(user.id)} botni ishga tushirdi (/start)")

async def token(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    ensure_user(user)
    
    # Kanalga obuna bo'lganligini tekshirish
    is_subscribed = await check_subscription(user.id, context)
    if not is_subscribed:
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("📢 Kanalga o'tish", url=CHANNEL_LINK)]
        ])
        txt = (
            f"<b>❗️ Bot funksiyalaridan foydalanish uchun kanalimizga obuna bo'ling.</b>\n\n"
            f"👉 Obuna bo'lgandan so'ng /start ni qayta bosing."
        )
        await update.message.reply_text(txt, parse_mode="HTML", reply_markup=keyboard)
        return
    
    # Referral link olish
    conn = db_conn()
    c = conn.cursor()
    c.execute("SELECT ref_link FROM users WHERE id=%s", (user.id,))
    row = c.fetchone()
    conn.close()
    
    if not row or not row[0]:
        ref_link = generate_random_link()
        save_user_link(user.id, ref_link)
    else:
        ref_link = row[0]
    
    txt = (
        "🎯 Token yig'ish uchun quyidagi havolani do'stlaringizga yuboring:\n\n"
        f"<a href='{ref_link}'>{ref_link}</a>\n\n"
        "💎 Do'stingiz kanalga a'zo bo'lganda 5 ta token olasiz!\n\n"
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
    
    # Obunani tekshirish
    if not await check_subscription_and_show_button(update, context):
        return
        
    tokens = get_tokens(user.id)
    refs = get_referrals(user.id)

    # referallar soni
    ref_count = len(refs) if refs else 0
    ref_text = f"{ref_count} ta odam" if ref_count > 0 else "Hech kim hali"

    conn = db_conn(); c = conn.cursor()
    c.execute("SELECT photo_active FROM users WHERE id=%s", (user.id,))
    is_photo_active = c.fetchone()[0]
    conn.close()

    if is_photo_active:
        status = (
            "🏅 Premium ta'rif faol!\n\n"
            "Siz yubora oladigan media turlar:\n"
            "📸 Rasmlar\n"
            "🎥 Videolar\n"
            "🎵 Audio/MP3\n"
            "🎤 Ovozli xabarlar"
        )
    else:
        status = (
            f"🔒 Premium ta'rif uchun {PHOTO_TOKEN_THRESHOLD} token kerak!\n\n"
            "Premium ta'rif orqali yubora oladigan media turlar:\n"
            "📸 Rasmlar\n"
            "🎥 Videolar\n"
            "🎵 Audio/MP3\n"
            "🎤 Ovozli xabarlar"
        )

    # 🔹 Tugma har doim chiqadi (token tekshirilmaydi)
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
    c.execute("SELECT id FROM users WHERE id=%s", (target_id,))
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
