# AI Use Declaration & Development Log

Module: UDE5014CM – Data Science for Developers
Project: Qamar Bookstore Weekly Book Demand Forecasting (Small Pilot Study)
Student: Abdulloh Abdulxamidov
Category: Green - AI Integrated (Coursework Brief Compliant)

---

## Log Entry 1: Baseline Architecture & Scraper MVP
* **Date:** 2026-10-20 (Teaching Week 6)
* **AI Tool Used:** Gemini / Claude
* **Purpose:**
  - Designing a normalized SQLite schema decoupling static book metadata from dynamic weekly observations.
  - Formulating regular expression patterns to extract pricing and reported weekly sales volume from Uzbek text structures.
  - Generating test scaffolding for Checkpoint 1 using `pytest`.

* **AI-Assisted Contributions:**
  1. Drafted initial SQLite table schemas (`books` and `weekly_observations`).
  2. Provided initial `re.search` patterns for parsing sales volume badges (`"so'nggi haftada ... dona sotildi"`).
  3. Suggested unit test patterns for input sanitation and database persistence.

* **Critical Human Review, Verification & Corrections:**
  1. **Schema Correction:** Modified foreign key cascading constraints and ensured observation timestamps adhere to `DATE` format with strict `UNIQUE(book_id, week_number)` constraints to enforce weekly snapshot integrity as required by the module leader.
  2. **Parser Bug Fix:** The initial AI-generated regex failed on `qamar.uz` due to the Uzbek apostrophe variant (tutuq belgisi: `'` vs `’` vs `` ` ``). Inspected the live DOM structure manually, corrected the regex tokenization, and successfully captured the dynamic badge (`74 dona sotildi`).
  3. **Test Isolation:** AI initially generated tests that wrote dummy records directly to the production `data/books.db`, polluting primary data. Rejected this implementation and refactored `test_database_persistence` to execute strictly against an isolated `:memory:` SQLite instance.

* **Outcome & Verification:**
  - 3 out of 3 automated unit tests passed successfully (`python -m pytest`).
  - Baseline primary data collection executed with rate-limiting (`time.sleep(2)`) and audit logging to `data/collection.log`.


---

## Log Entry 2: Week 6 Cohort Finalization
* **Date:** 2026-10-22 (Week 6)
* **Milestone:** Fixed Cohort (60 Books) Finalized & Baseline Snapshot Captured
* **Implementation Details:**
  1. Updated database schema in `src/database.py` to persist `raw_badge_text` as raw measurement evidence.
  2. Fixed SQL escape handling in `src/scraper.py` for text with apostrophes.
  3. Finalized 60 unique book URLs in `data/cohort_urls.txt` with verified rolling 7-day sales badges.
  4. Executed Week 6 baseline snapshot: 60 books and 60 non-null weekly observations stored in `data/books.db`.
  5. Verified code health with `pytest` (all 3 tests passed).