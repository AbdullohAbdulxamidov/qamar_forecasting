import os
import re
import time
import logging
import sqlite3
from datetime import date
import requests
from bs4 import BeautifulSoup

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(CURRENT_DIR, ".."))
LOG_FILE = os.path.join(PROJECT_ROOT, "data", "collection.log")
DB_PATH = os.path.join(PROJECT_ROOT, "data", "books.db")

os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

def clean_number(text: str):
    if not text:
        return None
    nums = re.findall(r"\d+", text.replace(" ", "").replace("\xa0", ""))
    return int("".join(nums)) if nums else None

def parse_book_page(url: str, week_number: int = 6):
    try:
        response = requests.get(url, headers=HEADERS, timeout=15)
        if response.status_code != 200:
            logging.error(f"Failed to fetch page: {url} (Status: {response.status_code})")
            return None

        soup = BeautifulSoup(response.text, "html.parser")
        page_text = soup.get_text()

        # 1. Title
        title_el = soup.find("h1") or soup.find("h2")
        title = title_el.get_text(strip=True) if title_el else "Noma'lum"

        # 2. Author (search layout below title)
        author = "Noma'lum"
        if title_el:
            next_sib = title_el.find_next_sibling()
            if next_sib and next_sib.get_text(strip=True):
                author = next_sib.get_text(strip=True)

        # 3. Price (price_uzs)
        price = None
        price_match = re.search(r"(\d[\d\s\xa0]*)\s*(?:so['’`]?m|UZS)", page_text, re.IGNORECASE)
        if price_match:
            price = clean_number(price_match.group(1))

        # 4. Weekly Sales & Exact Badge Text (Measurement Evidence)
        reported_sales = None
        raw_badge_text = None
        sales_pattern = r"(?:Xaridorgir\s+kitob\s*[-–—]\s*)?so['’`]?nggi\s+haftada\s+(\d+)\s+dona\s+sotildi"
        sales_match = re.search(sales_pattern, page_text, re.IGNORECASE)
        if sales_match:
            raw_badge_text = sales_match.group(0).strip()
            reported_sales = int(sales_match.group(1))

        # 5. Category Rank (#1-o'rin)
        category_rank = None
        rank_match = re.search(r"#(\d+)-o['’`]?rin", page_text, re.IGNORECASE)
        if rank_match:
            category_rank = int(rank_match.group(1))

        # 6. Physical Attributes & Metadata
        cover_type = "yumshoq"
        if "qattiq" in page_text.lower():
            cover_type = "qattiq"

        page_count = None
        pages_match = re.search(r"(\d+)\s*bet", page_text, re.IGNORECASE)
        if pages_match:
            page_count = int(pages_match.group(1))

        publisher = "Qamar"
        pub_match = re.search(r"Nashriyot\s*[:\n]*\s*([A-Za-z0-9_\-\s]+)", page_text)
        if pub_match:
            publisher = pub_match.group(1).split("\n")[0].strip()

        # Category from breadcrumbs or fallback
        category = "Badiiy bo'lmagan"
        breadcrumbs = soup.find_all(string=re.compile(r"Katalog\s*/", re.IGNORECASE))
        if breadcrumbs:
            parts = breadcrumbs[0].split("/")
            if len(parts) > 1:
                category = parts[1].strip()

        book_data = {
            "title": title,
            "author": author,
            "publisher": publisher,
            "category": category,
            "cover_type": cover_type,
            "page_count": page_count,
            "price_uzs": price,
            "reported_weekly_sales": reported_sales,
            "raw_badge_text": raw_badge_text,
            "category_rank": category_rank,
            "source_url": url,
            "week_number": week_number,
            "observation_date": str(date.today()),
            "is_in_stock": 1 if "sotuvda bor" in page_text.lower() else 0
        }

        logging.info(f"Parsed: {title} | Badge: {raw_badge_text} | Sales: {reported_sales}")
        return book_data

    except Exception as e:
        logging.error(f"Error scraping {url}: {str(e)}")
        return None

def save_to_database(data: dict):
    if not data:
        return False

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    try:
        cursor.execute("PRAGMA foreign_keys = ON;")

        # Kitob ma'lumotlarini saqlash (SQL ichida Noma'lum o'rniga parametr ishlatamiz)
        cursor.execute("""
            INSERT INTO books (title, author, publisher, category, cover_type, page_count, source_url)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(source_url) DO UPDATE SET
                title=excluded.title,
                author=CASE
                    WHEN excluded.author IS NOT NULL AND excluded.author != 'Noma''lum' THEN excluded.author
                    ELSE books.author
                END,
                publisher=excluded.publisher,
                category=excluded.category,
                cover_type=excluded.cover_type,
                page_count=coalesce(excluded.page_count, books.page_count)
        """, (
            data["title"], data["author"], data["publisher"], data["category"],
            data["cover_type"], data["page_count"], data["source_url"]
        ))

        cursor.execute("SELECT book_id FROM books WHERE source_url = ?", (data["source_url"],))
        book_id = cursor.fetchone()[0]

        # Haftalik kuzatuvni saqlash
        cursor.execute("""
            INSERT INTO weekly_observations
            (book_id, week_number, observation_date, price_uzs, reported_weekly_sales, raw_badge_text, category_rank, is_in_stock)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(book_id, week_number) DO UPDATE SET
                observation_date=excluded.observation_date,
                price_uzs=excluded.price_uzs,
                reported_weekly_sales=excluded.reported_weekly_sales,
                raw_badge_text=excluded.raw_badge_text,
                category_rank=excluded.category_rank,
                is_in_stock=excluded.is_in_stock
        """, (
            book_id, data["week_number"], data["observation_date"],
            data["price_uzs"], data["reported_weekly_sales"],
            data["raw_badge_text"],
            data["category_rank"], data["is_in_stock"]
        ))

        conn.commit()
        return True
    except Exception as e:
        logging.error(f"Bazaga yozishda xatolik: {str(e)}")
        conn.rollback()
        return False
    finally:
        conn.close()

if __name__ == "__main__":
    urls_file = os.path.join(PROJECT_ROOT, "data", "cohort_urls.txt")

    if os.path.exists(urls_file):
        with open(urls_file, "r", encoding="utf-8") as f:
            urls = [line.strip() for line in f if line.strip()]

        print(f"Jami {len(urls)} ta kitob skreyp qilinmoqda...")
        for idx, url in enumerate(urls, 1):
            print(f"[{idx}/{len(urls)}] O'qilmoqda: {url}")
            data = parse_book_page(url, week_number=6)
            if data:
                save_to_database(data)
                print(f"  -> Saqlandi: {data['title']} | Badge: '{data['raw_badge_text']}' | Sotuv: {data['reported_weekly_sales']}")
            time.sleep(2)
        print("\nBarcha kitoblar muvaffaqiyatli saqlandi!")
    else:
        print("data/cohort_urls.txt fayli topilmadi.")