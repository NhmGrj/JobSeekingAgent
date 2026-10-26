import html

import requests

SUBJECT_LABELS = {
    "jobs": "💼 Jobs",
    "freelance": "🧑‍💻 Freelance",
}


def send_message(bot_token: str, chat_id: str, text: str) -> None:
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "HTML",
        "disable_web_page_preview": True
    }
    response = requests.post(url, json=payload)
    if not response.ok:
        print(f"Telegram error: {response.text}")


def send_error(bot_token: str, chat_id: str, source_id: str, error: Exception) -> None:
    # Telegram caps messages at 4096 characters.
    message = html.escape(str(error)[:3500])
    send_message(
        bot_token, chat_id,
        f"⚠️ <b>Error — {html.escape(source_id)}</b>\n"
        f"<code>{html.escape(type(error).__name__)}</code>\n\n"
        f"<pre>{message}</pre>",
    )


def send_report(bot_token: str, chat_id: str, evaluated: list[dict]) -> None:
    """evaluated items: {subject, summary, url, score, verdict, explanation}"""
    apply = [e for e in evaluated if e["verdict"] == "APPLY"]
    maybe = [e for e in evaluated if e["verdict"] == "MAYBE"]

    if not apply and not maybe:
        send_message(bot_token, chat_id, "🤖 <b>Daily report</b>\n\nNothing new today.")
        return

    send_message(
        bot_token, chat_id,
        f"🤖 <b>Daily report</b>\n\n✅ {len(apply)} to apply\n🤔 {len(maybe)} maybe",
    )

    for entry in apply:
        label = SUBJECT_LABELS.get(entry["subject"], entry["subject"])
        send_message(
            bot_token, chat_id,
            f"✅ <b>APPLY — {entry['score']}/10</b> ({label})\n"
            f"<a href=\"{html.escape(entry['url'])}\">{html.escape(entry['summary'])}</a>\n"
            f"<i>{html.escape(entry['explanation'])}</i>"
        )

    for entry in maybe:
        label = SUBJECT_LABELS.get(entry["subject"], entry["subject"])
        send_message(
            bot_token, chat_id,
            f"🤔 <b>MAYBE — {entry['score']}/10</b> ({label})\n"
            f"<a href=\"{html.escape(entry['url'])}\">{html.escape(entry['summary'])}</a>\n"
            f"<i>{html.escape(entry['explanation'])}</i>"
        )

    print("Telegram notifications sent!")
