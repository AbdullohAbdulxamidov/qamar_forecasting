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