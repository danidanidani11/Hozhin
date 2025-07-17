import sqlite3
from contextlib import contextmanager

@contextmanager
def get_db():
    conn = sqlite3.connect('bot.db')
    try:
        yield conn
    finally:
        conn.close()

def init_db():
    with get_db() as conn:
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS users
                     (user_id INTEGER PRIMARY KEY, username TEXT, joined_channel BOOLEAN)''')
        c.execute('''CREATE TABLE IF NOT EXISTS receipts
                     (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, receipt_id TEXT, status TEXT)''')
        conn.commit()

def add_user(user_id, username):
    with get_db() as conn:
        c = conn.cursor()
        c.execute("INSERT OR REPLACE INTO users (user_id, username, joined_channel) VALUES (?, ?, ?)",
                  (user_id, username, False))
        conn.commit()

def update_channel_status(user_id, joined):
    with get_db() as conn:
        c = conn.cursor()
        c.execute("UPDATE users SET joined_channel = ? WHERE user_id = ?", (joined, user_id))
        conn.commit()

def get_user(user_id):
    with get_db() as conn:
        c = conn.cursor()
        c.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
        return c.fetchone()

def add_receipt(user_id, receipt_id):
    with get_db() as conn:
        c = conn.cursor()
        c.execute("INSERT INTO receipts (user_id, receipt_id, status) VALUES (?, ?, ?)",
                  (user_id, receipt_id, 'pending'))
        conn.commit()

def update_receipt_status(receipt_id, status):
    with get_db() as conn:
        c = conn.cursor()
        c.execute("UPDATE receipts SET status = ? WHERE receipt_id = ?", (status, receipt_id))
        conn.commit()

def get_receipt(receipt_id):
    with get_db() as conn:
        c = conn.cursor()
        c.execute("SELECT * FROM receipts WHERE receipt_id = ?", (receipt_id,))
        return c.fetchone()
