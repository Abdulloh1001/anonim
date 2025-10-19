import sqlite3
import time
from .config import DB_PATH

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY,
        username TEXT,
        first_name TEXT,
        created_at REAL,
        tokens INTEGER DEFAULT 0,
        photo_active INTEGER DEFAULT 0
    )""")
    c.execute("""CREATE TABLE IF NOT EXISTS referrals (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        referrer_id INTEGER,
        referred_id INTEGER,
        created_at REAL
    )""")
    c.execute("""CREATE TABLE IF NOT EXISTS anon_sessions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        owner_id INTEGER,
        anon_id INTEGER,
        created_at REAL
    )""")
    c.execute("""CREATE TABLE IF NOT EXISTS owner_notifications (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        owner_id INTEGER,
        anon_user_id INTEGER,
        owner_message_id INTEGER,
        created_at REAL
    )""")
    conn.commit()
    conn.close()

def db_conn():
    return sqlite3.connect(DB_PATH)
