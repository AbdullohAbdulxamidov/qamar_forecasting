import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "books.db")

def get_connection():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn

def init_db():
    conn = get_connection()
    cursor = conn.cursor()

    # 1. Kitoblarning o'zgarmas ma'lumotlari jadvali
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS books (
        book_id INTEGER PRIMARY KEY AUTOINCREMENT,
        isbn TEXT UNIQUE,
        title TEXT NOT NULL,
        author TEXT,
        publisher TEXT,
        category TEXT,
        cover_type TEXT,
        page_count INTEGER,
        source_url TEXT UNIQUE NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # 2. Har haftalik o'zgaruvchan kuzatuvlar jadvali
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS weekly_observations (
            obs_id INTEGER PRIMARY KEY AUTOINCREMENT,
            book_id INTEGER NOT NULL,
            week_number INTEGER NOT NULL,
            observation_date DATE NOT NULL,
            price_uzs REAL,
            reported_weekly_sales INTEGER,
            raw_badge_text TEXT,
            category_rank INTEGER,
            is_in_stock INTEGER DEFAULT 1,
            FOREIGN KEY (book_id) REFERENCES books (book_id) ON DELETE CASCADE,
            UNIQUE (book_id, week_number)
        );
        """)

    conn.commit()
    conn.close()
    print("Baza va jadvallar muvaffaqiyatli yaratildi: data/books.db")

if __name__ == "__main__":
    init_db()