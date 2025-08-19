import os
import time
import random
import psycopg2
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options

# ------------------ Database Setup ------------------
def setup_database():
    conn = psycopg2.connect(
        dbname="internship_assessment",
        user="postgres",
        password='kajalnaveen',  # ✅ use env variable
        host="localhost",
        port="5432"
    )
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS job_listings (
            id SERIAL PRIMARY KEY,
            job_title VARCHAR(255),
            company_name VARCHAR(255),
            location VARCHAR(255),
            job_url VARCHAR(512) UNIQUE,
            salary_info TEXT,
            job_description TEXT,
            source_site VARCHAR(100),
            scraped_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
        );
    """)
    conn.commit()
    return conn, cur


# ------------------ Browser Setup ------------------
def setup_driver():
    options = Options()
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("start-maximized")



    s = Service(r"D:\Github_Project\Delhi_Court\chromedriver.exe")
    driver = webdriver.Chrome(service=s, options=options)
    return driver


# ------------------ Detail Page Scraper ------------------
def scrape_detail_page(driver, job_url):
    """Open job in new tab, scrape description, close tab"""
    try:
        driver.execute_script("window.open(arguments[0], '_blank');", job_url)
        driver.switch_to.window(driver.window_handles[-1])

        # wait like a human
        time.sleep(5)  # ✅ fixed wait (not random)

        # scroll down slowly
        for _ in range(2):
            driver.execute_script("window.scrollBy(0, 800);")
            time.sleep(2)

        desc = driver.find_element(By.CSS_SELECTOR, "div#job-description").text.strip()
    except Exception:
        desc = None
    finally:
        driver.close()
        driver.switch_to.window(driver.window_handles[0])
    return desc


# ------------------ List Page Scraper ------------------
def scrape_list_page(driver, page_num):
    url = f"https://wellfound.com/role/data-analyst?page={page_num}"
    print(f"\n--- Scraping Page {page_num} ---")
    driver.get(url)

    # wait for jobs to render
    time.sleep(8)

    # scroll slowly like a human
    for _ in range(4):
        driver.execute_script("window.scrollBy(0, 1200);")
        time.sleep(random.uniform(2, 4))

    jobs_data = []
    jobs = driver.find_elements(By.CSS_SELECTOR, "div.mb-6.w-full.rounded.border.bg-white")

    for job in jobs:
        try:
            company = job.find_element(By.TAG_NAME, "h2").text
        except:
            company = None

        roles = job.find_elements(By.CSS_SELECTOR, "a.mr-2.text-sm.font-semibold.text-brand-burgandy")
        salary, location = None, None

        # salary + location
        extra_info = job.find_elements(By.CSS_SELECTOR, "span.pl-1.text-xs")
        for info in extra_info:
            text = info.text.strip()
            if "$" in text:
                salary = text
            elif "Remote" in text or "•" in text:
                location = text

        # loop through each role in one card
        for role in roles:
            title = role.text
            link = role.get_attribute("href")

            description = scrape_detail_page(driver, link)

            job_data = {
                "company": company,
                "title": title,
                "salary": salary,
                "location": location,
                "url": link,
                "description": description,
                "source_site": "Wellfound"
            }
            print(job_data)
            jobs_data.append(job_data)

            # wait between jobs
            time.sleep(random.uniform(6, 10))

    return jobs_data


# ------------------ Main ------------------
def main():
    conn, cur = setup_database()
    driver = setup_driver()
    all_jobs = []

    for page in range(1, 4):  # scrape 3 pages for test
        jobs = scrape_list_page(driver, page)
        all_jobs.extend(jobs)

        # insert into DB
        for job in jobs:
            try:
                cur.execute("""
                    INSERT INTO job_listings 
                    (job_title, company_name, location, job_url, salary_info, job_description, source_site)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (job_url) DO NOTHING
                """, (
                    job["title"], job["company"], job["location"], job["url"],
                    job["salary"], job["description"], job["source_site"]
                ))
                conn.commit()
            except Exception as e:
                print("DB insert error:", e)

        # ✅ cooldown before next page
        print(f"Sleeping before going to next page...")
        time.sleep(random.uniform(15, 25))

    driver.quit()
    cur.close()
    conn.close()
    print(f"\n✅ Total jobs scraped: {len(all_jobs)}")


if __name__ == "__main__":
    main()
