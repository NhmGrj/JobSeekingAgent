from sources.base import SourceDef

DEFAULT_CRITERIA = """
Tu es un assistant spécialisé dans la recherche d'emploi. Tu dois évaluer des offres d'emploi pour un candidat avec le profil suivant :

- 4 ans d'expérience en Product Management
- Recherche un poste de Product Manager (PM fortement préféré, Product Owner acceptable)
- Localisation : Paris uniquement, ou télétravail total
- Contrat : CDI uniquement
- Salaire minimum : 50 000€ brut annuel
- Expérience principale en B2B, intéressé par le B2C
- Télétravail fréquent ou total fortement préféré, occasionnel acceptable, pas de télétravail = malus mais pas éliminatoire

Pour chaque offre, tu dois retourner :
1. Un score de 1 à 10
2. Une courte explication (2-3 phrases max) des points positifs et négatifs
3. Un verdict : POSTULER, PEUT-ÊTRE, ou IGNORER

Réponds uniquement en JSON avec ce format :
{
  "score": 8,
  "explanation": "...",
  "verdict": "POSTULER"
}
"""


def login(page, creds: dict) -> None:
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
    page.fill('[data-testid="sign-in-form-email-input"]', creds["email"])
    page.wait_for_timeout(500)
    page.fill('[data-testid="sign-in-form-password-input"]', creds["password"])
    page.wait_for_timeout(500)
    page.click('[data-testid="sign-in-form-submit-button"]')

    page.wait_for_load_state("domcontentloaded")
    page.wait_for_timeout(3000)
    print("Logged in — current URL:", page.url)


def scrape(page, search_url: str, max_pages: int = 5) -> list[dict]:
    print("Navigating to job search...")
    page.goto(search_url, timeout=30000)
    page.wait_for_load_state("domcontentloaded")
    page.wait_for_selector('[data-testid="job-card-tag-location"]', timeout=10000)
    page.wait_for_timeout(2000)

    jobs = []

    for page_num in range(1, max_pages + 1):
        cards = page.query_selector_all(".bg-neutral-10.rounded-xl")
        print(f"Page {page_num} — Found {len(cards)} job cards")

        for card in cards:
            title_el = card.query_selector("a[href*='/jobs/']")
            if not title_el:
                continue

            company_el = card.query_selector("p")
            location_el = card.query_selector('[data-testid="job-card-tag-location"] span')
            contract_el = card.query_selector('[data-testid="job-card-tag-contract-type"] span')
            remote_el = card.query_selector('[data-testid="job-card-tag-remote"] span')

            jobs.append({
                "title": title_el.inner_text(),
                "company": company_el.inner_text() if company_el else "N/A",
                "location": location_el.inner_text() if location_el else "N/A",
                "contract": contract_el.inner_text() if contract_el else "N/A",
                "remote": remote_el.inner_text() if remote_el else "N/A",
                "url": "https://www.welcometothejungle.com" + title_el.get_attribute("href"),
            })

        try:
            next_button = page.query_selector('[data-testid="job-list-pagination-arrow-next"]')
            if not next_button or not next_button.is_enabled():
                print(f"No more pages after page {page_num}")
                break
            next_button.click()
            page.wait_for_load_state("domcontentloaded")
            page.wait_for_timeout(2000)
        except Exception as e:
            print(f"Pagination stopped: {e}")
            break

    print(f"Total jobs scraped: {len(jobs)}")
    return jobs


def item_key(item: dict) -> str:
    return f"{item['title']}|{item['company']}".lower().strip()


def format_summary(item: dict) -> str:
    return f"{item['title']} @ {item['company']} — {item['location']} | {item['contract']} | {item['remote']}"


SOURCE = SourceDef(
    platform="wttj",
    subject="jobs",
    login=login,
    scrape=scrape,
    item_key=item_key,
    format_summary=format_summary,
    default_criteria=DEFAULT_CRITERIA,
)
