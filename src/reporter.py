import requests
import os
from dotenv import load_dotenv

load_dotenv()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

def send_telegram(results: list[tuple]) -> None:
    postuler = [(job, r) for job, r in results if r['verdict'] == "POSTULER"]
    peut_etre = [(job, r) for job, r in results if r['verdict'] == "PEUT-ÊTRE"]

    message = "🤖 *Job Hunter — Rapport du jour*\n\n"

    if not postuler and not peut_etre:
        message += "Aucune nouvelle offre intéressante aujourd'hui."
    else:
        if postuler:
            message += f"✅ *POSTULER ({len(postuler)})*\n"
            for job, result in postuler:
                message += f"• [{job['title']} @ {job['company']}]({job['url']}) — {result['score']}/10\n"
                message += f"  _{result['explanation']}_\n\n"

        if peut_etre:
            message += f"🤔 *PEUT-ÊTRE ({len(peut_etre)})*\n"
            for job, result in peut_etre:
                message += f"• [{job['title']} @ {job['company']}]({job['url']}) — {result['score']}/10\n"
                message += f"  _{result['explanation']}_\n\n"

    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "Markdown",
        "disable_web_page_preview": True
    }

    response = requests.post(url, json=payload)
    if response.ok:
        print("Telegram notification sent!")
    else:
        print(f"Telegram error: {response.text}")