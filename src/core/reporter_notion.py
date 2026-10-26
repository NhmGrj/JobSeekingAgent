import requests
import os
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

# Not wired into main.py — kept for a possible return to Notion.
# TODO when re-enabling: property names and select values were translated to English
# (2026-10-26) and no longer match the existing Notion database. Rename its columns
# (or these keys) before use:
#   Titre -> Title, Entreprise -> Company, Localisation -> Location, Contrat -> Contract,
#   Télétravail -> Remote, Statut -> Status, Analyse -> Analysis
#   Status options: "À postuler" -> "To apply", "À évaluer" -> "To review"
#   Verdict options: POSTULER/PEUT-ÊTRE -> APPLY/MAYBE

NOTION_TOKEN = os.getenv("NOTION_TOKEN")
NOTION_DATABASE_ID = os.getenv("NOTION_DATABASE_ID")

HEADERS = {
    "Authorization": f"Bearer {NOTION_TOKEN}",
    "Content-Type": "application/json",
    "Notion-Version": "2022-06-28"
}

def append_jobs(results: list[tuple]) -> None:
    for job, result in results:
        if result["verdict"] not in ["APPLY", "MAYBE"]:
            continue

        status = "To apply" if result["verdict"] == "APPLY" else "To review"

        payload = {
            "parent": {"database_id": NOTION_DATABASE_ID},
            "properties": {
                "Title": {
                    "title": [{"text": {"content": job["title"]}}]
                },
                "Company": {
                    "rich_text": [{"text": {"content": job["company"]}}]
                },
                "Score": {
                    "number": result["score"]
                },
                "Verdict": {
                    "select": {"name": result["verdict"]}
                },
                "Location": {
                    "rich_text": [{"text": {"content": job["location"]}}]
                },
                "Contract": {
                    "rich_text": [{"text": {"content": job["contract"]}}]
                },
                "Remote": {
                    "rich_text": [{"text": {"content": job["remote"]}}]
                },
                "URL": {
                    "url": job["url"]
                },
                "Status": {
                    "select": {"name": status}
                },
                "Analysis": {
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