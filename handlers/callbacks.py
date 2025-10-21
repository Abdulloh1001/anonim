from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from core.utils import get_tokens, db_conn, display_for, log_channel_send
from core.config import PHOTO_TOKEN_THRESHOLD, REF_REWARD, CHANNEL_LINK
from core.channel import check_subscription, generate_random_link, save_user_link

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user = query.from_user
    tokens = get_tokens(user.id)

    if query.data == "check_subscription":
        is_subscribed = await check_subscription(user.id, context)
        if not is_subscribed:
            await query.answer("❌ Siz hali kanalga obuna bo'lmadingiz!", show_alert=True)
            return

        # ✅ Obuna bo‘lgan bo‘lsa:
        await query.answer("✅ Obuna tekshirildi!", show_alert=True)

        # Foydalanuvchini bazada qayd etamiz
        from core.utils import ensure_user
        ensure_user(user)

        # Referral link yaratamiz
        from core.channel import generate_random_link, save_user_link
        ref_link = generate_random_link()
        save_user_link(user.id, ref_link)

        # Foydalanuvchiga tabrik xabar
        text = (
            f"🎉 Tabriklaymiz, {user.first_name}!\n\n"
            f"Endi bot funksiyalaridan to‘liq foydalansangiz bo‘ladi.\n\n"
            f"📎 Sizning referal havolangiz:\n<a href='{ref_link}'>{ref_link}</a>\n\n"
            f"💰 Token yig‘ish uchun /token buyrug‘ini bosing.\n"
            f"📊 Balansni tekshirish uchun /balans buyrug‘ini bosing."
        )
        await query.message.edit_text(text, parse_mode="HTML")

    elif query.data == "show_token_info":
        # Obunani tekshirish
        is_subscribed = await check_subscription(user.id, context)
        if not is_subscribed:
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("📢 Kanalga o'tish", url=CHANNEL_LINK)],
                [InlineKeyboardButton("✅ Obuna bo'ldim", callback_data="check_subscription")]
            ])
            txt = (
                f"❗️ Bot funksiyalaridan foydalanish uchun kanalimizga obuna bo'ling.\n\n"
                f"👉 Obuna bo'lgandan so'ng \"✅ Obuna bo'ldim\" tugmasini bosing."
            )
            await query.message.edit_text(txt, parse_mode="HTML", reply_markup=keyboard)
            return

        tokens = get_tokens(user.id)
        txt = (
            f"💎 Token yig'ish bo'yicha qo'llanma:\n\n"
            f"1. Referral havolangizni do'stlaringizga yuboring\n"
            f"2. Ular kanalga a'zo bo'lishganda siz {REF_REWARD} token olasiz\n"
            f"3. {PHOTO_TOKEN_THRESHOLD} token to'plagach premium xususiyatlarni yoqing\n\n"
            f"💰 Joriy balansingiz: {tokens} token"
        )
        await query.message.edit_text(txt, parse_mode="HTML")

    elif query.data == "activate_photo":
        # Obunani tekshirish
        is_subscribed = await check_subscription(user.id, context)
        if not is_subscribed:
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("📢 Kanalga o'tish", url=CHANNEL_LINK)],
                [InlineKeyboardButton("✅ Obuna bo'ldim", callback_data="check_subscription")]
            ])
            txt = (
                f"❗️ Bot funksiyalaridan foydalanish uchun kanalimizga obuna bo'ling.\n\n"
                f"👉 Obuna bo'lgandan so'ng \"✅ Obuna bo'ldim\" tugmasini bosing."
            )
            await query.message.edit_text(txt, parse_mode="HTML", reply_markup=keyboard)
            return

        if tokens < PHOTO_TOKEN_THRESHOLD:
            await query.edit_message_text(
                f"❌ Token yetarli emas.\n\n"
                f"💰 Joriy balansingiz: {tokens} token\n"
                f"🎯 Kerak: {PHOTO_TOKEN_THRESHOLD} token"
            )
        else:
            conn = db_conn(); c = conn.cursor()
            c.execute("SELECT photo_active FROM users WHERE id=%s", (user.id,))
            already_active = c.fetchone()[0]
            if already_active:
                await query.edit_message_text("❗ Ta'rif allaqachon faol.")
            else:
                c.execute("UPDATE users SET photo_active=1, tokens=tokens-%s WHERE id=%s", (PHOTO_TOKEN_THRESHOLD, user.id))
                conn.commit()
                await query.edit_message_text(
                    "✅ Ta'rif faollashtirildi! Endi siz quyidagilarni yubora olasiz:\n\n"
                    "📸 Rasmlar\n"
                    "🎥 Videolar\n"
                    "🎵 Audio/MP3\n"
                    "🎤 Ovozli xabarlar"
                )
                await log_channel_send(context.bot, f"{display_for(user.id)} premium ta'rifni faollashtirdi ✅")
            conn.close()