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


---

## Log Entry 3: Week 7 Longitudinal Snapshot Captured
* **Date:** 2026-10-31 (Teaching Week 7)
* **Milestone:** Second Longitudinal Observation Completed
* **Implementation Details:**
  1. Updated scraper target week to `week_number=7`.
  2. Executed non-destructive crawl across the fixed 60-book cohort without resetting database.
  3. Stored 60 new observations in `weekly_observations` table in `data/books.db` (total dataset: 120 observations).
  4. Observed real-world dynamic sales shifts (e.g., volume spikes and normal rolling decay).
  5. Handled edge cases where rolling badges temporarily dropped below reportable thresholds (stored as NULLs preserving longitudinal integrity).
  6. Verified test suite integrity with `pytest` (3 passed).


---

## Log Entry 4: Observation Snapshot 3 Captured (Calendar Week 8 / Reading Week)
* **Date:** 2026-11-08 (End of Reading Week)
* **Milestone:** Third Longitudinal Observation Wave Finalized (180 Total Observations)
* **Implementation Details:**
  1. Maintained strict 7-day rolling cadence ($\Delta t \approx 7 \text{ days}$) across the academic calendar by collecting data during university Reading Week.
  2. Recorded under `week_number=8` to preserve temporal progression for validation modeling.
  3. Captured 60 records across the fixed cohort: observed active market shifts (e.g., "Ko'zlaringni haromdan saqla" surging to 287 units, "D bo'limi" stabilizing to 155 units).
  4. Non-reporting books handled as missing badge values (`NULL`), protecting cohort integrity without data leakage.
  5. Test suite verified via `pytest` (all 3 tests passing).