from telegram.ext import ContextTypes
from telegram import ChatMember
import random
import string
from .db import db_conn
from .config import CHANNEL_ID

async def check_subscription(user_id: int, context: ContextTypes.DEFAULT_TYPE) -> bool:
    """Foydalanuvchi kanalga obuna bo'lganligini tekshirish"""
    try:
        member = await context.bot.get_chat_member(chat_id=CHANNEL_ID, user_id=user_id)
        return member.status in [ChatMember.MEMBER, ChatMember.ADMINISTRATOR, ChatMember.CREATOR]
    except Exception:
        return False

def generate_random_link():
    """Random link generatsiya qilish"""
    chars = string.ascii_letters + string.digits
    random_suffix = ''.join(random.choice(chars) for _ in range(10))
    return f"t.me/{CHANNEL_ID}/{random_suffix}"

def save_user_link(user_id: int, link: str):
    """Foydalanuvchi linkini saqlash"""
    conn = db_conn()
    c = conn.cursor()
    c.execute("UPDATE users SET ref_link=%s WHERE id=%s", (link, user_id))
    conn.commit()
    conn.close()

def get_referrer_by_link(link: str):
    """Link orqali referal egasini topish"""
    conn = db_conn()
    c = conn.cursor()
    c.execute("SELECT id FROM users WHERE ref_link=%s", (link,))
    row = c.fetchone()
    conn.close()
    return row[0] if row else None