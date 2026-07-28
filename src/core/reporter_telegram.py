import requests

SUBJECT_LABELS = {
    "jobs": "💼 Jobs",
    "apartments": "🏠 Appartements",
}


def send_message(bot_token: str, chat_id: str, text: str) -> None:
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "Markdown",
        "disable_web_page_preview": True
    }
    response = requests.post(url, json=payload)
    if not response.ok:
        print(f"Telegram error: {response.text}")


def send_report(bot_token: str, chat_id: str, evaluated: list[dict]) -> None:
    """evaluated items: {subject, summary, url, score, verdict, explanation}"""
    postuler = [e for e in evaluated if e["verdict"] == "POSTULER"]
    peut_etre = [e for e in evaluated if e["verdict"] == "PEUT-ÊTRE"]

    if not postuler and not peut_etre:
        send_message(bot_token, chat_id, "🤖 *Rapport du jour*\n\nRien de nouveau aujourd'hui.")
        return

    send_message(
        bot_token, chat_id,
        f"🤖 *Rapport du jour*\n\n✅ {len(postuler)} à postuler\n🤔 {len(peut_etre)} peut-être",
    )

    for entry in postuler:
        label = SUBJECT_LABELS.get(entry["subject"], entry["subject"])
        send_message(
            bot_token, chat_id,
            f"✅ *POSTULER — {entry['score']}/10* ({label})\n"
            f"[{entry['summary']}]({entry['url']})\n"
            f"_{entry['explanation']}_"
        )

    for entry in peut_etre:
        label = SUBJECT_LABELS.get(entry["subject"], entry["subject"])
        send_message(
            bot_token, chat_id,
            f"🤔 *PEUT-ÊTRE — {entry['score']}/10* ({label})\n"
            f"[{entry['summary']}]({entry['url']})\n"
            f"_{entry['explanation']}_"
        )

    print("Telegram notifications sent!")
