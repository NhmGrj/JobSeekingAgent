import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "../seen_jobs.db")

def init_db():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS seen_jobs (
            title_company TEXT PRIMARY KEY,
            url TEXT,
            title TEXT,
            company TEXT,
            seen_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()

def is_seen(title: str, company: str) -> bool:
    conn = sqlite3.connect(DB_PATH)
    key = f"{title}|{company}".lower().strip()
    result = conn.execute("SELECT 1 FROM seen_jobs WHERE title_company = ?", (key,)).fetchone()
    conn.close()
    return result is not None

def mark_seen(url: str, title: str, company: str):
    conn = sqlite3.connect(DB_PATH)
    key = f"{title}|{company}".lower().strip()
    conn.execute("INSERT OR IGNORE INTO seen_jobs (title_company, url, title, company) VALUES (?, ?, ?, ?)", (key, url, title, company))
    conn.commit()
    conn.close()