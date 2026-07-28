import requests
import os
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

NOTION_TOKEN = os.getenv("NOTION_TOKEN")
NOTION_DATABASE_ID = os.getenv("NOTION_DATABASE_ID")

HEADERS = {
    "Authorization": f"Bearer {NOTION_TOKEN}",
    "Content-Type": "application/json",
    "Notion-Version": "2022-06-28"
}

def append_jobs(results: list[tuple]) -> None:
    for job, result in results:
        if result["verdict"] not in ["POSTULER", "PEUT-ÊTRE"]:
            continue

        statut = "À postuler" if result["verdict"] == "POSTULER" else "À évaluer"

        payload = {
            "parent": {"database_id": NOTION_DATABASE_ID},
            "properties": {
                "Titre": {
                    "title": [{"text": {"content": job["title"]}}]
                },
                "Entreprise": {
                    "rich_text": [{"text": {"content": job["company"]}}]
                },
                "Score": {
                    "number": result["score"]
                },
                "Verdict": {
                    "select": {"name": result["verdict"]}
                },
                "Localisation": {
                    "rich_text": [{"text": {"content": job["location"]}}]
                },
                "Contrat": {
                    "rich_text": [{"text": {"content": job["contract"]}}]
                },
                "Télétravail": {
                    "rich_text": [{"text": {"content": job["remote"]}}]
                },
                "URL": {
                    "url": job["url"]
                },
                "Statut": {
                    "select": {"name": statut}
                },
                "Analyse": {
                    "rich_text": [{"text": {"content": result["explanation"]}}]
                },
                "Date": {
                    "date": {"start": datetime.now().strftime("%Y-%m-%d")}
                }
            }
        }

        response = requests.post(
            "https://api.notion.com/v1/pages",
            headers=HEADERS,
            json=payload
        )

        if response.ok:
            print(f"Notion: added {job['title']} @ {job['company']}")
        else:
            print(f"Notion error: {response.text}")