import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "../../seen_jobs.db")


def init_db():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS seen_items (
            user_id TEXT NOT NULL,
            source_id TEXT NOT NULL,
            item_key TEXT NOT NULL,
            url TEXT,
            label TEXT,
            seen_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (user_id, source_id, item_key)
        )
    """)

    legacy_exists = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='seen_jobs'"
    ).fetchone()
    if legacy_exists:
        already_migrated = conn.execute(
            "SELECT 1 FROM seen_items WHERE source_id = 'wttj_jobs' LIMIT 1"
        ).fetchone()
        if not already_migrated:
            cur = conn.execute("""
                INSERT OR IGNORE INTO seen_items (user_id, source_id, item_key, url, label, seen_at)
                SELECT 'nhm', 'wttj_jobs', title_company, url, title || ' @ ' || company, seen_at
                FROM seen_jobs
            """)
            print(f"Migrated {cur.rowcount} legacy rows from seen_jobs into seen_items")

    conn.commit()
    conn.close()


def is_seen(user_id: str, source_id: str, item_key: str) -> bool:
    conn = sqlite3.connect(DB_PATH)
    result = conn.execute(
        "SELECT 1 FROM seen_items WHERE user_id = ? AND source_id = ? AND item_key = ?",
        (user_id, source_id, item_key),
    ).fetchone()
    conn.close()
    return result is not None


def mark_seen(user_id: str, source_id: str, item_key: str, url: str, label: str) -> None:
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        "INSERT OR IGNORE INTO seen_items (user_id, source_id, item_key, url, label) VALUES (?, ?, ?, ?, ?)",
        (user_id, source_id, item_key, url, label),
    )
    conn.commit()
    conn.close()
