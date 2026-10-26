from dotenv import load_dotenv
load_dotenv()

import os

from playwright.sync_api import sync_playwright

import config
from core import database, evaluator, reporter_telegram, results_writer

# WTTJ's CDN returns 403 to the default "HeadlessChrome" user agent (since 2026-10-02).
USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36"
)


def run_source(page, user: config.UserConfig, source: config.SourceConfig) -> list[dict]:
    creds = {field: os.environ[env_name] for field, env_name in source.credentials_env.items()}
    source.source_def.login(page, creds)
    items = source.source_def.scrape(page, source.search_url, source.max_pages)

    new_items = [
        item for item in items
        if not database.is_seen(user.id, source.id, source.source_def.item_key(item))
    ]
    print(f"[{user.id}/{source.id}] {len(items)} found, {len(new_items)} new to evaluate")

    # One request for the whole batch; if it raises, nothing is marked seen and
    # every item is retried on the next run.
    results = evaluator.evaluate_items(new_items, source.criteria)

    evaluated = []
    for item, result in zip(new_items, results):
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

    return evaluated


def run_user(browser, user: config.UserConfig) -> bool:
    bot_token = os.environ[user.telegram_token_env]
    chat_id = os.environ[user.telegram_chat_id_env]

    ok = True
    all_evaluated = []
    for source in user.sources:
        context = browser.new_context(user_agent=USER_AGENT)
        try:
            all_evaluated.extend(run_source(context.new_page(), user, source))
        except Exception as e:
            print(f"[{user.id}/{source.id}] ERROR: {e}")
            reporter_telegram.send_error(bot_token, chat_id, source.id, e)
            ok = False
        finally:
            context.close()

    # Skip "nothing new today" when the only news is an error already reported.
    if ok or all_evaluated:
        reporter_telegram.send_report(bot_token, chat_id, all_evaluated)

    path = results_writer.write_markdown(user.id, all_evaluated)
    print(f"[{user.id}] Results saved to {path}")
    return ok


def main() -> int:
    config.validate_config(config.USERS)
    database.init_db()

    ok = True
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        try:
            for user in config.USERS:
                try:
                    ok = run_user(browser, user) and ok
                except Exception as e:
                    print(f"[{user.id}] ERROR: {e}")
                    ok = False
        finally:
            browser.close()

    # Non-zero exit so the CI run shows as failed instead of silently green.
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
