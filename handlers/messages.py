from telegram import Update
from telegram.ext import ContextTypes
from core.utils import ensure_user, find_owner_for_anon, get_anon_from_reply, save_notification, display_for, log_channel_send
from core.db import db_conn

from core.channel import get_referrer_by_link

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message
    user = msg.from_user
    ensure_user(user)

    # egasi anonimga javob yozgan bo'lsa
    if msg.reply_to_message:
        anon_id = get_anon_from_reply(user.id, msg.reply_to_message.message_id)
        if anon_id:
            await context.bot.send_message(chat_id=anon_id, text=msg.text)
            await msg.reply_text("✅ Xabaringiz anonim foydalanuvchiga yuborildi.")
            await log_channel_send(context.bot, f"{display_for(user.id)} ➡️ {display_for(anon_id)}: {msg.text}")
        return

    # Foydalanuvchi havolasini olish
    conn = db_conn()
    c = conn.cursor()
    c.execute("SELECT ref_link FROM users WHERE id=%s", (user.id,))
    row = c.fetchone()
    conn.close()
    
    if not row or not row[0]:
        await msg.reply_text("❗ Iltimos, avval /start buyrug'ini bosing.")
        return
        
    # O'zining havolasi orqali yuborilgan xabarni o'ziga qaytarish
    sent = await context.bot.send_message(chat_id=user.id, text=f"🕶 Anonimdan: {msg.text}")
    save_notification(user.id, user.id, sent.message_id)
    await msg.reply_text("✅ Xabaringiz yuborildi.")
    await log_channel_send(context.bot, f"{display_for(user.id)} → o'ziga: {msg.text}")

async def handle_media(update: Update, context: ContextTypes.DEFAULT_TYPE, media_type="media"):
    """Universal media handler"""
    msg = update.message
    user = msg.from_user
    ensure_user(user)
    
    # Media yuborishga ruxsat berish
    if not user:
        await msg.reply_text("❌ Xatolik yuz berdi. Qayta urinib ko'ring.")
        return

    # Anonim chatni tekshirish
    owner_id = find_owner_for_anon(user.id)
    if not owner_id:
        await msg.reply_text("❗ Siz anonim suhbatga ulanmagansiz.")
        return

    try:
        if media_type == "photo":
            file_id = msg.photo[-1].file_id
            sent = await context.bot.send_photo(chat_id=owner_id, photo=file_id, caption="🕶 Anonimdan rasm")
            media_emoji = "📸"
        elif media_type == "sticker":
            file_id = msg.sticker.file_id
            sent = await context.bot.send_sticker(chat_id=owner_id, sticker=file_id)
            media_emoji = "🎯"
        elif media_type == "video":
            file_id = msg.video.file_id
            sent = await context.bot.send_video(chat_id=owner_id, video=file_id, caption="🕶 Anonimdan video")
            media_emoji = "🎥"
        elif media_type == "voice":
            file_id = msg.voice.file_id
            sent = await context.bot.send_voice(chat_id=owner_id, voice=file_id, caption="🕶 Anonimdan ovozli xabar")
            media_emoji = "🎤"
        elif media_type == "audio":
            file_id = msg.audio.file_id
            caption = f"🕶 Anonimdan audio\n"
            if msg.audio.title:
                caption += f"📄 Nomi: {msg.audio.title}\n"
            if msg.audio.performer:
                caption += f"🎵 Ijrochi: {msg.audio.performer}"
            sent = await context.bot.send_audio(chat_id=owner_id, audio=file_id, caption=caption)
            media_emoji = "🎵"
        
        save_notification(owner_id, user.id, sent.message_id)
        await msg.reply_text("✅ Media yuborildi.")
        await log_channel_send(context.bot, f"{display_for(user.id)} {media_emoji} {media_type} yubordi → {display_for(owner_id)}")
    
    except Exception as e:
        await msg.reply_text(f"❌ Xatolik yuz berdi: {str(e)}")

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await handle_media(update, context, "photo")

async def handle_sticker(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await handle_media(update, context, "sticker")

async def handle_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await handle_media(update, context, "video")

async def handle_voice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await handle_media(update, context, "voice")

async def handle_audio(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await handle_media(update, context, "audio")
