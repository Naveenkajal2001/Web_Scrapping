# Web Scraper for Wellfound (formerly AngelList)

This Python project scrapes job listings for Web Scrapper roles from [Wellfound.com](https://wellfound.com), extracts detailed job info, and stores the results in a PostgreSQL database.

---

## 📌 Overview

- Uses **Selenium** to automate a headless browser and bypass JavaScript-based anti-bot protections.
- Scrapes multiple pages of job listings.
- Opens each job in a new tab to extract detailed descriptions.
- Stores job data into a **PostgreSQL** database, avoiding duplicates via a unique URL constraint.
- Mimics human browsing with scrolling, tab switching, and random delays.

---


