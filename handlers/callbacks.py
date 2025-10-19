from telegram import Update
from telegram.ext import ContextTypes
from core.utils import get_tokens, db_conn, display_for, log_channel_send
from core.config import PHOTO_TOKEN_THRESHOLD

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user = query.from_user
    tokens = get_tokens(user.id)

    if query.data == "activate_photo":
        if tokens < PHOTO_TOKEN_THRESHOLD:
            await query.edit_message_text("❌ Token yetarli emas.")
        else:
            conn = db_conn(); c = conn.cursor()
            c.execute("SELECT photo_active FROM users WHERE id=?", (user.id,))
            already_active = c.fetchone()[0]
            if already_active:
                await query.edit_message_text("❗ Ta'rif allaqachon faol.")
            else:
                c.execute("UPDATE users SET photo_active=1, tokens=tokens-? WHERE id=?", (PHOTO_TOKEN_THRESHOLD, user.id))
                conn.commit()
                await query.edit_message_text(
                    "✅ Ta'rif faollashtirildi! Endi siz quyidagilarni yubora olasiz:\n\n"
                    "📸 Rasmlar\n"
                    "🎯 Stikerlar\n"
                    "🎥 Videolar\n"
                    "🎵 Audio/MP3\n"
                    "🎤 Ovozli xabarlar"
                )
                await log_channel_send(context.bot, f"{display_for(user.id)} premium ta'rifni faollashtirdi ✅")
            conn.close()