import os
import sqlite3
import pytest
from src.scraper import clean_number, save_to_database, DB_PATH

# 1-test: Valid input (Raqamlarni matndan to'g'ri tozalab olish)
def test_clean_number_valid():
    assert clean_number("54 000 so'm") == 54000
    assert clean_number("74 dona") == 74
    assert clean_number("240 bet") == 240

# 2-test: Invalid input / Edge case (Bo'sh yoki xato qiymatlar)
def test_clean_number_invalid():
    assert clean_number(None) is None
    assert clean_number("") is None
    assert clean_number("Matn ichida son yo'q") is None

# 3-test: Persistence and Provenance (Bazaga yozish va qayta o'qish)
def test_database_persistence():
    sample_data = {
        "title": "Test Kitob",
        "author": "Test Muallif",
        "publisher": "Test Nashriyot",
        "category": "Test Kategoriya",
        "cover_type": "yumshoq",
        "page_count": 150,
        "price_uzs": 45000,
        "reported_weekly_sales": 25,
        "category_rank": 5,
        "source_url": "https://qamar.uz/kitob/test-kitob-unique-url",
        "week_number": 6,
        "observation_date": "2026-10-20",
        "is_in_stock": 1
    }

    # Bazaga yozish
    success = save_to_database(sample_data)
    assert success is True

    # Bazadan qayta o'qib tekshirish
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT title, price_uzs FROM books JOIN weekly_observations USING(book_id) WHERE source_url = ?", (sample_data["source_url"],))
    row = cursor.fetchone()
    conn.close()

    assert row is not None
    assert row[0] == "Test Kitob"
    assert row[1] == 45000