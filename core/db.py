import psycopg2
import psycopg2.extras
import time
import os

DB_URL = os.getenv("DATABASE_URL")  # Railway dagi DATABASE_URL

def init_db():
    conn = psycopg2.connect(DB_URL)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id BIGINT PRIMARY KEY,
            username TEXT,
            first_name TEXT,
            created_at DOUBLE PRECISION,
            tokens INTEGER DEFAULT 0,
            photo_active INTEGER DEFAULT 0
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS referrals (
            id SERIAL PRIMARY KEY,
            referrer_id BIGINT,
            referred_id BIGINT,
            created_at DOUBLE PRECISION
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS anon_sessions (
            id SERIAL PRIMARY KEY,
            owner_id BIGINT,
            anon_id BIGINT,
            created_at DOUBLE PRECISION
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS owner_notifications (
            id SERIAL PRIMARY KEY,
            owner_id BIGINT,
            anon_user_id BIGINT,
            owner_message_id BIGINT,
            created_at DOUBLE PRECISION
        )
    """)
    conn.commit()
    conn.close()

def db_conn():
    return psycopg2.connect(DB_URL, cursor_factory=psycopg2.extras.DictCursor)
