import sqlite3
import pytest
from src.scraper import clean_number

# 1-test: Sonlarni tozalash funksiyasi
def test_clean_number_valid():
    assert clean_number("54 000 so'm") == 54000
    assert clean_number("74 dona") == 74
    assert clean_number("240 bet") == 240

# 2-test: Noto'g'ri qiymatlarni qayta ishlash
def test_clean_number_invalid():
    assert clean_number(None) is None
    assert clean_number("") is None
    assert clean_number("Matn ichida son yo'q") is None

# 3-test: Ma'lumotlar bazasi saqlanishi (In-Memory: Asosiy books.db ga tegmaydi)
def test_database_persistence_in_memory():
    conn = sqlite3.connect(":memory:")
    cursor = conn.cursor()

    # Asosiy jadvallar nusxasi
    cursor.execute("""
    CREATE TABLE books (
        book_id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        author TEXT,
        publisher TEXT,
        category TEXT,
        cover_type TEXT,
        page_count INTEGER,
        source_url TEXT UNIQUE NOT NULL
    );
    """)
    cursor.execute("""
    CREATE TABLE weekly_observations (
        obs_id INTEGER PRIMARY KEY AUTOINCREMENT,
        book_id INTEGER NOT NULL,
        week_number INTEGER NOT NULL,
        observation_date DATE NOT NULL,
        price_uzs REAL,
        reported_weekly_sales INTEGER,
        raw_badge_text TEXT,
        category_rank INTEGER,
        is_in_stock INTEGER DEFAULT 1,
        FOREIGN KEY (book_id) REFERENCES books (book_id),
        UNIQUE (book_id, week_number)
    );
    """)

    # Namuna ma'lumot kiritish
    cursor.execute("""
        INSERT INTO books (title, author, publisher, category, cover_type, page_count, source_url)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, ("Test Kitob", "Test Muallif", "Test Nashriyot", "Test Kategoriya", "yumshoq", 150, "https://qamar.uz/kitob/test-kitob"))

    cursor.execute("SELECT book_id FROM books WHERE source_url = ?", ("https://qamar.uz/kitob/test-kitob",))
    book_id = cursor.fetchone()[0]

    cursor.execute("""
        INSERT INTO weekly_observations
        (book_id, week_number, observation_date, price_uzs, reported_weekly_sales, raw_badge_text, category_rank, is_in_stock)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (book_id, 6, "2026-10-21", 45000, 25, "so'nggi haftada 25 dona sotildi", 5, 1))

    conn.commit()

    # Saqlanganligini tekshirish
    cursor.execute("SELECT b.title, w.price_uzs, w.raw_badge_text FROM books b JOIN weekly_observations w USING(book_id)")
    row = cursor.fetchone()
    conn.close()

    assert row is not None
    assert row[0] == "Test Kitob"
    assert row[1] == 45000
    assert row[2] == "so'nggi haftada 25 dona sotildi"