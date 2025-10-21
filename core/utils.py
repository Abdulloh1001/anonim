import hmac, hashlib, time, asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from .db import db_conn
from .config import SECRET_KEY, LOG_CHANNEL_ID, CHANNEL_LINK
from .channel import check_subscription

ALPH = "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"

def b62encode(n: int) -> str:
    if n == 0: return ALPH[0]
    s=[]
    while n>0:
        s.append(ALPH[n%62]); n//=62
    return ''.join(reversed(s))

def make_payload(user_id: int) -> str:
    uid_part = b62encode(user_id)
    hm = hmac.new(SECRET_KEY.encode(), str(user_id).encode(), hashlib.sha256).digest()
    short = int.from_bytes(hm[:6], 'big')
    return uid_part + b62encode(short)

def parse_payload(payload: str):
    for i in range(1, len(payload)):
        pref = payload[:i]; rest = payload[i:]
        try:
            uid = 0
            for ch in pref: uid = uid*62 + ALPH.index(ch)
        except ValueError:
            continue
        hm = hmac.new(SECRET_KEY.encode(), str(uid).encode(), hashlib.sha256).digest()
        short = int.from_bytes(hm[:6], 'big')
        if rest == b62encode(short):
            return uid
    return None

def ensure_user(u):
    conn = db_conn(); c = conn.cursor()
    c.execute("SELECT id FROM users WHERE id=%s", (u.id,))
    new_user = False
    if c.fetchone() is None:
        c.execute("INSERT INTO users (id, username, first_name, created_at, tokens, photo_active) VALUES (%s,%s,%s,%s,%s,%s)",
                  (u.id, u.username, u.first_name or "", time.time(), 0, 0))
        new_user = True
    else:
        c.execute("UPDATE users SET username=%s, first_name=%s WHERE id=%s", (u.username, u.first_name or "", u.id))
    conn.commit(); conn.close()
    return new_user

def get_tokens(uid):
    conn=db_conn();c=conn.cursor()
    c.execute("SELECT tokens FROM users WHERE id=%s", (uid,))
    r=c.fetchone();conn.close()
    return r[0] if r else 0

def add_tokens(uid, n):
    conn=db_conn();c=conn.cursor()
    c.execute("SELECT tokens FROM users WHERE id=%s", (uid,))
    r=c.fetchone(); prev=r[0] if r else 0
    new=prev+n
    c.execute("UPDATE users SET tokens=%s WHERE id=%s", (new, uid))
    conn.commit();conn.close()
    return prev,new

def display_for(u_id: int):
    conn = db_conn(); c = conn.cursor()
    c.execute("SELECT username, first_name FROM users WHERE id=%s", (u_id,))
    row = c.fetchone()
    conn.close()
    
    if not row:
        return f'<a href="tg://user?id={u_id}">ID:{u_id}</a>'

    username, first_name = row

    if username:
        return f'<a href="https://t.me/{username}">@{username}</a>'
    elif first_name:
        safe_name = first_name.replace("<", "").replace(">", "")
        return f'<a href="tg://user?id={u_id}">{safe_name}</a>'
    else:
        return f'<a href="tg://user?id={u_id}">ID:{u_id}</a>'

def find_owner_for_anon(anon_id):
    conn = db_conn(); c = conn.cursor()
    c.execute("SELECT owner_id FROM anon_sessions WHERE anon_id=%s ORDER BY id DESC LIMIT 1", (anon_id,))
    r = c.fetchone(); conn.close()
    return r[0] if r else None

def save_notification(owner_id, anon_user_id, owner_message_id):
    conn = db_conn(); c = conn.cursor()
    c.execute("INSERT INTO owner_notifications (owner_id, anon_user_id, owner_message_id, created_at) VALUES (%s,%s,%s,%s)",
              (owner_id, anon_user_id, owner_message_id, time.time()))
    conn.commit(); conn.close()

def get_anon_from_reply(owner_id, owner_message_id):
    conn = db_conn(); c = conn.cursor()
    c.execute("SELECT anon_user_id FROM owner_notifications WHERE owner_id=%s AND owner_message_id=%s ORDER BY id DESC LIMIT 1",
              (owner_id, owner_message_id))
    r = c.fetchone(); conn.close()
    return r[0] if r else None

def get_referrals(owner_id):
    conn = db_conn(); c = conn.cursor()
    c.execute("SELECT referred_id FROM referrals WHERE referrer_id=%s", (owner_id,))
    rows = [r[0] for r in c.fetchall()]
    conn.close(); return rows

def add_referral(owner_id, new_user_id):
    conn = db_conn()
    c = conn.cursor()
    c.execute("SELECT 1 FROM referrals WHERE referrer_id=%s AND referred_id=%s", (owner_id, new_user_id))
    exists = c.fetchone()
    if exists:
        conn.close()
        return False
    c.execute("INSERT INTO referrals (referrer_id, referred_id, created_at) VALUES (%s,%s,%s)",
            (owner_id, new_user_id, time.time()))
    conn.commit()
    conn.close()
    return True

def record_session(owner_id, anon_id):
    conn = db_conn()
    c = conn.cursor()
    c.execute("SELECT id FROM anon_sessions WHERE owner_id=%s AND anon_id=%s", (owner_id, anon_id))
    exists = c.fetchone()
    if not exists:
        c.execute("INSERT INTO anon_sessions (owner_id, anon_id, created_at) VALUES (%s,%s,%s)",
                (owner_id, anon_id, time.time()))
        conn.commit()
    conn.close()

_last_log_time = 0

async def check_subscription_and_show_button(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    """Obunani tekshirish va obuna bo'lish tugmasini ko'rsatish"""
    user = update.effective_user
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
        await update.message.reply_text(txt, parse_mode="HTML", reply_markup=keyboard)
        return False
    return True

async def log_channel_send(bot, text):
    global _last_log_time
    if not LOG_CHANNEL_ID:
        print(f"LOG_CHANNEL_ID topilmadi")
        return

    now = time.time()
    if now - _last_log_time < 1:
        await asyncio.sleep(1)

    try:
        print(f"Log yuborilmoqda: ID={LOG_CHANNEL_ID}, text={text}")
        await bot.send_message(
            chat_id=int(LOG_CHANNEL_ID),
            text=text,
            parse_mode="HTML",
            disable_web_page_preview=True
        )
        print("Log muvaffaqiyatli yuborildi")
        _last_log_time = time.time()
    except Exception as e:
        print(f"Log yuborishda xatolik: {str(e)}")
