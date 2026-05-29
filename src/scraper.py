from playwright.sync_api import sync_playwright
from dotenv import load_dotenv
import os

load_dotenv()

def login(page):
    print("Opening WTTJ...")
    page.goto("https://www.welcometothejungle.com/fr/authenticate/signin", timeout=30000)
    page.wait_for_load_state("domcontentloaded")

    print("Dismissing cookie banner...")
    try:
        page.wait_for_selector("#axeptio_btn_acceptAll", timeout=5000)
        page.click("#axeptio_btn_acceptAll")
        page.wait_for_timeout(1000)
        print("Cookie banner dismissed")
    except:
        print("No cookie banner found, continuing...")

    print("Filling login form...")
    page.wait_for_selector('[data-testid="sign-in-form-email-input"]')
    page.fill('[data-testid="sign-in-form-email-input"]', os.getenv("WTTJ_EMAIL"))
    page.wait_for_timeout(500)
    page.fill('[data-testid="sign-in-form-password-input"]', os.getenv("WTTJ_PASSWORD"))
    page.wait_for_timeout(500)
    page.click('[data-testid="sign-in-form-submit-button"]')

    page.wait_for_load_state("domcontentloaded")
    page.wait_for_timeout(3000)
    print("Logged in — current URL:", page.url)

def scrape_jobs(page, search_url: str) -> list[dict]:
    print(f"Navigating to job search...")
    page.goto(search_url, timeout=30000)
    page.wait_for_load_state("domcontentloaded")
    page.wait_for_selector('[data-testid="job-card-tag-location"]', timeout=10000)
    page.wait_for_timeout(2000)
    page.screenshot(path="debug.png")

    jobs = []
    cards = page.query_selector_all(".bg-neutral-10.rounded-xl")

    print(f"Found {len(cards)} job cards")

    for card in cards:
        title_el = card.query_selector("a[href*='/jobs/']")
        company_el = card.query_selector("p")
        location_el = card.query_selector('[data-testid="job-card-tag-location"] span')
        contract_el = card.query_selector('[data-testid="job-card-tag-contract-type"] span')
        remote_el = card.query_selector('[data-testid="job-card-tag-remote"] span')

        jobs.append({
            "title": title_el.inner_text() if title_el else "N/A",
            "company": company_el.inner_text() if company_el else "N/A",
            "location": location_el.inner_text() if location_el else "N/A",
            "contract": contract_el.inner_text() if contract_el else "N/A",
            "remote": remote_el.inner_text() if remote_el else "N/A",
            "url": "https://www.welcometothejungle.com" + title_el.get_attribute("href") if title_el else "N/A",
        })

    return jobs

def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        login(page)

        jobs = scrape_jobs(page, "https://www.welcometothejungle.com/fr/jobs-matches")

        for job in jobs:
            print(f"\n{job['title']} — {job['company']}")
            print(f"  {job['location']} | {job['contract']} | {job['remote']}")
            print(f"  {job['url']}")

        browser.close()

main()