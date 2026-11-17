import sqlite3
from contextlib import contextmanager
from pathlib import Path
from ..core.config import get_settings

def db_path() -> str:
    return get_settings().database_url.removeprefix("sqlite:///")

@contextmanager
def connection():
    conn = sqlite3.connect(db_path())
    conn.row_factory = sqlite3.Row
    try: yield conn
    finally: conn.close()

def initialize_database():
    Path(db_path()).parent.mkdir(parents=True, exist_ok=True)
    with connection() as db:
        db.executescript("""
        CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, name TEXT NOT NULL, email TEXT UNIQUE NOT NULL, password_hash TEXT NOT NULL, created_at TEXT DEFAULT CURRENT_TIMESTAMP);
        CREATE TABLE IF NOT EXISTS posts (id INTEGER PRIMARY KEY, user_id INTEGER NOT NULL, content TEXT NOT NULL, platform TEXT NOT NULL, impressions INTEGER DEFAULT 0, engagement INTEGER DEFAULT 0, created_at TEXT DEFAULT CURRENT_TIMESTAMP, FOREIGN KEY(user_id) REFERENCES users(id));
        """)
        db.commit()
