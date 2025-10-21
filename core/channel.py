from core.db import db_conn

def get_referrer_by_link(link: str):
    """Link orqali referal egasini topish"""
    conn = db_conn()
    c = conn.cursor()
    c.execute("SELECT id FROM users WHERE ref_link=%s", (link,))
    row = c.fetchone()
    conn.close()
    return row[0] if row else None