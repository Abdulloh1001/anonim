from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, CallbackQueryHandler
from core.db import init_db
from handlers.commands import start, help_cmd, balans, give_tokens, token
from handlers.messages import handle_text, handle_photo, handle_sticker, handle_video, handle_voice, handle_audio
from handlers.callbacks import handle_callback
from core.config import BOT_TOKEN

def main():
    if not BOT_TOKEN:
        print("Please set BOT_TOKEN in .env")
        return

    init_db()
    app = ApplicationBuilder().token(BOT_TOKEN).connect_timeout(10).read_timeout(10).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("token", token))
    app.add_handler(CommandHandler("balans", balans))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(CommandHandler("give_tokens", give_tokens))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    app.add_handler(MessageHandler(filters.PHOTO & ~filters.COMMAND, handle_photo))
    app.add_handler(MessageHandler(filters.Sticker.ALL & ~filters.COMMAND, handle_sticker))
    app.add_handler(MessageHandler(filters.VIDEO & ~filters.COMMAND, handle_video))
    app.add_handler(MessageHandler(filters.VOICE & ~filters.COMMAND, handle_voice))
    app.add_handler(MessageHandler(filters.AUDIO & ~filters.COMMAND, handle_audio))
    app.add_handler(CallbackQueryHandler(handle_callback))

    print("🤖 Bot ishga tushdi...")
    app.run_polling()

if __name__ == "__main__":
    import threading
    from admin_server import run_server
    
    # Admin panel serverini alohida threadda ishga tushirish
    admin_thread = threading.Thread(target=run_server)
    admin_thread.daemon = True
    admin_thread.start()
    
    # Asosiy botni ishga tushirish
    main()
