import requests
import os
from dotenv import load_dotenv

load_dotenv()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

def send_message(text: str) -> None:
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": text,
        "parse_mode": "Markdown",
        "disable_web_page_preview": True
    }
    response = requests.post(url, json=payload)
    if not response.ok:
        print(f"Telegram error: {response.text}")

def send_telegram(results: list[tuple]) -> None:
    postuler = [(job, r) for job, r in results if r['verdict'] == "POSTULER"]
    peut_etre = [(job, r) for job, r in results if r['verdict'] == "PEUT-ÊTRE"]

    if not postuler and not peut_etre:
        send_message("🤖 *Job Hunter — Rapport du jour*\n\nAucune nouvelle offre intéressante aujourd'hui.")
        return

    send_message(f"🤖 *Job Hunter — Rapport du jour*\n\n✅ {len(postuler)} à postuler\n🤔 {len(peut_etre)} peut-être")

    for job, result in postuler:
        send_message(
            f"✅ *POSTULER — {result['score']}/10*\n"
            f"[{job['title']} @ {job['company']}]({job['url']})\n"
            f"📍 {job['location']} | {job['contract']} | {job['remote']}\n"
            f"_{result['explanation']}_"
        )

    for job, result in peut_etre:
        send_message(
            f"🤔 *PEUT-ÊTRE — {result['score']}/10*\n"
            f"[{job['title']} @ {job['company']}]({job['url']})\n"
            f"📍 {job['location']} | {job['contract']} | {job['remote']}\n"
            f"_{result['explanation']}_"
        )

    print("Telegram notifications sent!")