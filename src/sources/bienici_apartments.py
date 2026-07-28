from sources.base import SourceDef

# Not wired into config.USERS yet — this only proves the SourceDef shape compiles.
# Expected item dict shape once implemented, e.g.:
#   {"title": str, "city": str, "price": str, "surface": str, "rooms": str, "url": str}

DEFAULT_CRITERIA = "TODO: critères de recherche d'appartement (budget, quartier, surface, nombre de pièces, etc.)"


def login(page, creds: dict) -> None:
    raise NotImplementedError("TODO: flux d'authentification Bien'ici")


def scrape(page, search_url: str, max_pages: int = 5) -> list[dict]:
    raise NotImplementedError("TODO: sélecteurs de la liste d'annonces Bien'ici")


def item_key(item: dict) -> str:
    return item.get("url", "").lower().strip()


def format_summary(item: dict) -> str:
    return f"{item.get('title', 'N/A')} — {item.get('city', 'N/A')} — {item.get('price', 'N/A')}"


SOURCE = SourceDef(
    platform="bienici",
    subject="apartments",
    login=login,
    scrape=scrape,
    item_key=item_key,
    format_summary=format_summary,
    default_criteria=DEFAULT_CRITERIA,
)
