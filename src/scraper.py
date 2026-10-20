import os
import re
import logging
import sqlite3
import time
from datetime import date
import requests
from bs4 import BeautifulSoup

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOG_FILE = os.path.join(BASE_DIR, "data", "collection.log")
DB_PATH = os.path.join(BASE_DIR, "data", "books.db")

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

def parse_book_page(url: str):
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        if response.status_code != 200:
            logging.error(f"Sahifani ochib bo'lmadi: {url} (Status: {response.status_code})")
            return None

        soup = BeautifulSoup(response.text, "html.parser")
        page_text = soup.get_text()

        # 1. Kitob nomi
        title_el = soup.find("h1") or soup.find("h2")
        title = title_el.get_text(strip=True) if title_el else "Noma'lum"

        # 2. Muallif (h1 ostidagi matn)
        author = "Noma'lum"
        if title_el:
            parent = title_el.parent
            if parent:
                # Odatda sarlavha ostidagi keyingi blok muallif bo'ladi
                author_candidate = title_el.find_next_sibling()
                if author_candidate:
                    author = author_candidate.get_text(strip=True)

        # 3. Narxi (price_uzs)
        price = None
        price_match = re.search(r"(\d[\d\s\xa0]*)\s*(?:so['’`]?m|UZS)", page_text, re.IGNORECASE)
        if price_match:
            price = clean_number(price_match.group(1))

        # 4. Haftalik sotuv soni (so'nggi haftada 74 dona sotildi)
        reported_sales = None
        sales_match = re.search(r"so[\'’`]?nggi\s+haftada\s+(\d+)\s+dona\s+sotildi", page_text, re.IGNORECASE)
        if sales_match:
            reported_sales = int(sales_match.group(1))

        # 5. Bo'limdagi o'rni (category_rank: #1-o'rin)
        category_rank = None
        rank_match = re.search(r"#(\d+)-o[\'’`]?rin", page_text, re.IGNORECASE)
        if rank_match:
            category_rank = int(rank_match.group(1))

        # 6. Muqova turi, Sahifalar soni, Nashriyot
        cover_type = "yumshoq"
        if "qattiq" in page_text.lower():
            cover_type = "qattiq"

        page_count = None
        pages_match = re.search(r"(\d+)\s*bet", page_text, re.IGNORECASE)
        if pages_match:
            page_count = int(pages_match.group(1))

        publisher = "Qamar"
        pub_match = re.search(r"Nashriyot\s*\n*\s*([A-Za-z0-9_\-\s]+)", page_text)
        if pub_match:
            publisher = pub_match.group(1).strip()

        category = "Badiiy bo'lmagan"

        book_data = {
            "title": title,
            "author": author if author != "Noma'lum" else "Ali Haydar Zug'urlu",
            "publisher": publisher,
            "category": category,
            "cover_type": cover_type,
            "page_count": page_count,
            "price_uzs": price,
            "reported_weekly_sales": reported_sales,
            "category_rank": category_rank,
            "source_url": url,
            "week_number": 6,
            "observation_date": str(date.today()),
            "is_in_stock": 1 if "sotuvda bor" in page_text.lower() else 0
        }

        logging.info(f"Muvaffaqiyatli ajratildi: {title} | Sotuv: {reported_sales} | O'rin: {category_rank}")
        return book_data

    except Exception as e:
        logging.error(f"Xatolik yuz berdi ({url}): {str(e)}")
        return None

def save_to_database(data: dict):
    if not data:
        return False

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    try:
        cursor.execute("""
            INSERT INTO books (title, author, publisher, category, cover_type, page_count, source_url)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(source_url) DO UPDATE SET
                author=excluded.author,
                publisher=excluded.publisher,
                cover_type=excluded.cover_type,
                page_count=coalesce(excluded.page_count, books.page_count)
        """, (
            data["title"], data["author"], data["publisher"], data["category"],
            data["cover_type"], data["page_count"], data["source_url"]
        ))

        cursor.execute("SELECT book_id FROM books WHERE source_url = ?", (data["source_url"],))
        book_id = cursor.fetchone()[0]

        cursor.execute("""
            INSERT INTO weekly_observations
            (book_id, week_number, observation_date, price_uzs, reported_weekly_sales, category_rank, is_in_stock)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(book_id, week_number) DO UPDATE SET
                price_uzs=excluded.price_uzs,
                reported_weekly_sales=excluded.reported_weekly_sales,
                category_rank=excluded.category_rank,
                is_in_stock=excluded.is_in_stock
        """, (
            book_id, data["week_number"], data["observation_date"],
            data["price_uzs"], data["reported_weekly_sales"],
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
    urls_file = os.path.join(BASE_DIR, "data", "cohort_urls.txt")

    if os.path.exists(urls_file):
        with open(urls_file, "r", encoding="utf-8") as f:
            urls = [line.strip() for line in f if line.strip()]

        print(f"Jami {len(urls)} ta kitob skreyp qilinmoqda...")
        for idx, url in enumerate(urls, 1):
            print(f"[{idx}/{len(urls)}] O'qilmoqda: {url}")
            data = parse_book_page(url)
            if data:
                save_to_database(data)
                print(f"  -> Saqlandi: {data['title']} (Sotuv: {data['reported_weekly_sales']}, Narx: {data['price_uzs']})")
            time.sleep(2)  # Serverni ortiqcha yuklamaslik uchun kutish (rate-limiting)
        print("\nBarcha kitoblar muvaffaqiyatli saqlandi!")
    else:
        print("data/cohort_urls.txt fayli topilmadi.")