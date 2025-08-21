import time
import psycopg2
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options

# Database Setup
def setup_database():
    conn = psycopg2.connect(
        dbname="internship_assessment",
        user="postgres",
        password='kajalnaveen',
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


def setup_driver():
    options = Options()
    # options.add_argument("--headless") # Do not working in headless mode
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("start-maximized")



    s = Service(r"D:\Github_Project\Delhi_Court\chromedriver.exe")
    driver = webdriver.Chrome(service=s, options=options)
    return driver


def scrape_page(driver, page_num):
    url = f"https://wellfound.com/role/data-analyst?page={page_num}"
    print(f"\n--- Scraping Page {page_num} ---")
    driver.get(url)

    # wait for jobs to render
    time.sleep(5)

    # Scroll to show human behaviour
    driver.execute_script("window.scrollBy(0, 1200);")
    time.sleep(2)

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

            job_data = {
                "company": company,
                "title": title,
                "salary": salary,
                "location": location,
                "url": link,
                "source_site": "Wellfound"
            }
            # print(job_data)
            jobs_data.append(job_data)

    return jobs_data

def about(joblist):

    for index, job in enumerate(joblist):
        url = job['url']

        a = setup_driver()
        a.get(url)
        time.sleep(5)
        print(url)

        try:
            desc = a.find_element(By.ID, "job-description").text.strip()
        except Exception:
            desc = None

        joblist[index]['description'] = desc
        a.quit()

    return joblist

def main():
    conn, cur = setup_database()
    driver = setup_driver()
    all_jobs = []

    for page in range(1, 3): 
        jobs = scrape_page(driver, page)
        all_jobs.extend(jobs)
    # print(all_jobs)
    driver.quit()
    about_page = about(all_jobs)
        # insert into DB
    for job in about_page:
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
            print("Job is inserted: ",job)
        except Exception as e:
            print("DB insert error:", e)


    driver.quit()
    cur.close()
    conn.close()
    


if __name__ == "__main__":
    main()
