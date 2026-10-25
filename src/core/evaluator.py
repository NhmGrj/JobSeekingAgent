from google import genai
from google.genai import types
import os
import json

MODEL = "gemini-3.8-flash"

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


def evaluate_items(items: list[dict], criteria: str) -> list[dict]:
    """Evaluates all items in a single request; returns one result per item, in order.

    Raises on any failure (API error, unparseable or incomplete response) so the
    caller can report it; nothing is retried.
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

    response = _get_client().models.generate_content(
        model=MODEL,
        contents=prompt,
        config=types.GenerateContentConfig(
            system_instruction=criteria,
            response_mime_type="application/json",
            response_json_schema=RESPONSE_SCHEMA,
        ),
    )
    results = {r["index"]: r for r in json.loads(response.text)}

    missing = [i for i in range(len(items)) if i not in results]
    if missing:
        raise ValueError(f"Réponse Gemini incomplète : éléments manquants {missing}")

    return [
        {k: results[i][k] for k in ("score", "explanation", "verdict")}
        for i in range(len(items))
    ]
