import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
LOG_CHANNEL_ID = os.getenv("LOG_CHANNEL_ID")
CHANNEL_USERNAME = os.getenv("CHANNEL_USERNAME", "eclipse_1oo1")  # Kanal usernamesi @ belgisisiz
CHANNEL_ID = os.getenv("CHANNEL_ID", "-100123456789")  # O'z kanal ID raqamingizni kiriting
SECRET_KEY = os.getenv("SECRET_KEY", "anon123")
REF_REWARD = 5
PHOTO_TOKEN_THRESHOLD = 50
DB_PATH = "anon_bot.db"

# Kanal havolasi
CHANNEL_LINK = f"https://t.me/{CHANNEL_USERNAME}"
