from dataclasses import dataclass
from typing import Callable


@dataclass(frozen=True)
class SourceDef:
    """Contract a sources/*.py module implements and exports as a module-level SOURCE.

    login(page, creds: dict) -> None
    scrape(page, search_url: str, max_pages: int) -> list[dict]
    item_key(item: dict) -> str          # stable dedup key within this source
    format_summary(item: dict) -> str    # one-liner for messages/markdown
    """

    platform: str
    subject: str
    login: Callable
    scrape: Callable
    item_key: Callable
    format_summary: Callable
    default_criteria: str
