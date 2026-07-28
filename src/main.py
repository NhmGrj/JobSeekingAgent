from dotenv import load_dotenv
load_dotenv()

import os
import time

from playwright.sync_api import sync_playwright

import config
from core import database, evaluator, reporter_telegram, results_writer


def run_source(page, user: config.UserConfig, source: config.SourceConfig) -> list[dict]:
    creds = {field: os.environ[env_name] for field, env_name in source.credentials_env.items()}
    source.source_def.login(page, creds)
    items = source.source_def.scrape(page, source.search_url, source.max_pages)

    new_items = [
        item for item in items
        if not database.is_seen(user.id, source.id, source.source_def.item_key(item))
    ]
    print(f"[{user.id}/{source.id}] {len(items)} trouvés, {len(new_items)} nouveaux à évaluer")

    evaluated = []
    for i, item in enumerate(new_items):
        result = evaluator.evaluate_item(item, source.criteria)
        key = source.source_def.item_key(item)
        summary = source.source_def.format_summary(item)
        database.mark_seen(user.id, source.id, key, item.get("url", ""), summary)
        evaluated.append({
            "subject": source.subject,
            "summary": summary,
            "url": item.get("url", ""),
            **result,
        })
        print(f"{result['verdict']} ({result['score']}/10) — {summary}")
        if i < len(new_items) - 1:
            time.sleep(3)

    return evaluated


def run_user(browser, user: config.UserConfig) -> None:
    all_evaluated = []
    for source in user.sources:
        context = browser.new_context()
        try:
            all_evaluated.extend(run_source(context.new_page(), user, source))
        except Exception as e:
            print(f"[{user.id}/{source.id}] ERROR: {e}")
        finally:
            context.close()

    bot_token = os.environ[user.telegram_token_env]
    chat_id = os.environ[user.telegram_chat_id_env]
    reporter_telegram.send_report(bot_token, chat_id, all_evaluated)

    path = results_writer.write_markdown(user.id, all_evaluated)
    print(f"[{user.id}] Résultats sauvegardés dans {path}")


def main():
    config.validate_config(config.USERS)
    database.init_db()

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        try:
            for user in config.USERS:
                try:
                    run_user(browser, user)
                except Exception as e:
                    print(f"[{user.id}] ERROR: {e}")
        finally:
            browser.close()


if __name__ == "__main__":
    main()
