from scraper import scrape_jobs, login
from evaluator import evaluate_job
from database import init_db, is_seen, mark_seen
from playwright.sync_api import sync_playwright
from datetime import datetime

def main():
    init_db()

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        login(page)
        jobs = scrape_jobs(page, "https://www.welcometothejungle.com/fr/jobs-matches")
        browser.close()

    new_jobs = [job for job in jobs if job['title'] != "N/A" and not is_seen(job['url'])]

    print(f"\n{len(jobs) - 1} offres trouvées, {len(new_jobs)} nouvelles à évaluer\n")

    if not new_jobs:
        print("Aucune nouvelle offre aujourd'hui !")
        return

    results = []
    for job in new_jobs:
        result = evaluate_job(job)
        mark_seen(job['url'], job['title'], job['company'])
        results.append((job, result))
        print(f"{result['verdict']} ({result['score']}/10) — {job['title']} @ {job['company']}")

    date_str = datetime.now().strftime("%Y-%m-%d_%H-%M")
    output_path = f"../results_{date_str}.md"

    with open(output_path, "w") as f:
        f.write(f"# Résultats du {datetime.now().strftime('%d/%m/%Y %H:%M')}\n\n")

        for verdict in ["POSTULER", "PEUT-ÊTRE", "IGNORER"]:
            f.write(f"## {verdict}\n\n")
            for job, result in results:
                if result['verdict'] == verdict:
                    f.write(f"### {job['title']} @ {job['company']}\n")
                    f.write(f"- **Score:** {result['score']}/10\n")
                    f.write(f"- **Localisation:** {job['location']} | {job['contract']} | {job['remote']}\n")
                    f.write(f"- **Analyse:** {result['explanation']}\n")
                    f.write(f"- **URL:** {job['url']}\n\n")

    print(f"\nRésultats sauvegardés dans {output_path}")

main()