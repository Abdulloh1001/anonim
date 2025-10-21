import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
LOG_CHANNEL_ID = os.getenv("LOG_CHANNEL_ID")
CHANNEL_ID = os.getenv("CHANNEL_ID")  # Majburiy obuna uchun kanal ID
CHANNEL_LINK = os.getenv("CHANNEL_LINK")  # Kanal linki
SECRET_KEY = os.getenv("SECRET_KEY", "anon123")
REF_REWARD = 5
PHOTO_TOKEN_THRESHOLD = 50
DB_PATH = "anon_bot.db"
