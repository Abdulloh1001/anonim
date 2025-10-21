"""

Callback functions for bot buttons
"""
from telegram import Update
from telegram.ext import ContextTypes
from core.utils import ensure_user, display_for, log_channel_send
from core.channel import generate_random_link, save_user_link

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle callback queries from inline buttons"""
    query = update.callback_query
    await query.answer()
    user = query.from_user
    
    if query.data == "get_link":
        # Foydalanuvchini bazada qayd etamiz
        ensure_user(user)

        # Yangi havola yaratamiz
        ref_link = generate_random_link()
        save_user_link(user.id, ref_link)

        # Foydalanuvchiga havolani yuboramiz
        text = (
            f"🔗 Sizning shaxsiy havolangiz:\n"
            f"<a href='{ref_link}'>{ref_link}</a>\n\n"
            "Bu havola orqali sizga anonim xabarlar yuborishadi!"
        )
        await query.message.edit_text(text, parse_mode="HTML")
        await log_channel_send(context.bot, f"{display_for(user.id)} yangi havola yaratdi")