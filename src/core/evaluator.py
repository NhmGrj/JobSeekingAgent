from google import genai
from google.genai import errors, types
import os
import json
import time

MODEL = "gemini-3.8-flash"

# Gemini's free tier regularly answers 503 "high demand"; these spikes are
# transient, so we keep retrying for up to an hour before giving up for the day.
RETRY_CODES = {500, 503, 504}
RETRY_BUDGET_SECONDS = 60 * 60
RETRY_DELAYS_SECONDS = [60, 120, 240, 480]  # then RETRY_MAX_DELAY_SECONDS
RETRY_MAX_DELAY_SECONDS = 15 * 60

RESPONSE_SCHEMA = {
    "type": "array",
    "items": {
        "type": "object",
        "properties": {
            "index": {"type": "integer"},
            "score": {"type": "integer", "minimum": 1, "maximum": 10},
            "explanation": {"type": "string"},
            "verdict": {"type": "string", "enum": ["POSTULER", "PEUT-ÊTRE", "IGNORER"]},
        },
        "required": ["index", "score", "explanation", "verdict"],
    },
}

_client = None


def _get_client() -> genai.Client:
    global _client
    if _client is None:
        _client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
    return _client


def _generate_with_retry(prompt: str, criteria: str):
    """Calls Gemini, retrying transient server errors (5xx) for up to RETRY_BUDGET_SECONDS.

    Any other error is raised immediately.
    """
    start = time.monotonic()
    attempt = 0
    while True:
        attempt += 1
        try:
            return _get_client().models.generate_content(
                model=MODEL,
                contents=prompt,
                config=types.GenerateContentConfig(
                    system_instruction=criteria,
                    response_mime_type="application/json",
                    response_json_schema=RESPONSE_SCHEMA,
                ),
            )
        except errors.APIError as e:
            if e.code not in RETRY_CODES:
                raise
            delay = RETRY_DELAYS_SECONDS[attempt - 1] if attempt <= len(RETRY_DELAYS_SECONDS) else RETRY_MAX_DELAY_SECONDS
            elapsed = time.monotonic() - start
            if elapsed >= RETRY_BUDGET_SECONDS:
                raise RuntimeError(
                    f"Gemini indisponible depuis {round(elapsed / 60)} min "
                    f"({attempt} tentatives), abandon pour aujourd'hui. Dernière erreur : {e}"
                ) from e
            print(f"Gemini {e.code} (tentative {attempt}), nouvel essai dans {delay // 60} min")
            time.sleep(delay)


def evaluate_items(items: list[dict], criteria: str) -> list[dict]:
    """Evaluates all items in a single request; returns one result per item, in order.

    Transient Gemini server errors are retried (see _generate_with_retry); any
    other failure (API error, unparseable or incomplete response) is raised so
    the caller can report it.
    """
    if not items:
        return []

    blocks = []
    for i, item in enumerate(items):
        fields = "\n".join(f"- {k}: {v}" for k, v in item.items())
        blocks.append(f"### Élément {i}\n{fields}")
    prompt = f"""
Voici {len(items)} éléments à évaluer, numérotés de 0 à {len(items) - 1} :

{chr(10).join(blocks)}

Évalue chaque élément selon les critères fournis. Réponds avec une liste JSON
contenant un objet par élément, avec son "index", son "score", son "explanation"
et son "verdict".
"""

    response = _generate_with_retry(prompt, criteria)
    results = {r["index"]: r for r in json.loads(response.text)}

    missing = [i for i in range(len(items)) if i not in results]
    if missing:
        raise ValueError(f"Réponse Gemini incomplète : éléments manquants {missing}")

    return [
        {k: results[i][k] for k in ("score", "explanation", "verdict")}
        for i in range(len(items))
    ]
