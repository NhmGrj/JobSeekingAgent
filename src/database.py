import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "../seen_jobs.db")

def init_db():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS seen_jobs (
            url TEXT PRIMARY KEY,
            title TEXT,
            company TEXT,
            seen_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()

def is_seen(url: str) -> bool:
    conn = sqlite3.connect(DB_PATH)
    result = conn.execute("SELECT 1 FROM seen_jobs WHERE url = ?", (url,)).fetchone()
    conn.close()
    return result is not None

def mark_seen(url: str, title: str, company: str):
    conn = sqlite3.connect(DB_PATH)
    conn.execute("INSERT OR IGNORE INTO seen_jobs (url, title, company) VALUES (?, ?, ?)", (url, title, company))
    conn.commit()
    conn.close()