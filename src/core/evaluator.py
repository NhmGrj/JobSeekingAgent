from google import genai
from google.genai import errors, types
import os
import json
import time

MODEL = "gemini-3.8-flash"

RESPONSE_SCHEMA = {
    "type": "object",
    "properties": {
        "score": {"type": "integer", "minimum": 1, "maximum": 10},
        "explanation": {"type": "string"},
        "verdict": {"type": "string", "enum": ["POSTULER", "PEUT-ÊTRE", "IGNORER"]},
    },
    "required": ["score", "explanation", "verdict"],
}

_client = None


def _get_client() -> genai.Client:
    global _client
    if _client is None:
        _client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
    return _client


def evaluate_item(item: dict, criteria: str, retries: int = 3, delay: int = 10) -> dict:
    fields = "\n".join(f"- {k}: {v}" for k, v in item.items())
    prompt = f"""
Voici un élément à évaluer :
{fields}

Évalue cet élément selon les critères fournis.
"""

    for attempt in range(retries):
        try:
            response = _get_client().models.generate_content(
                model=MODEL,
                contents=prompt,
                config=types.GenerateContentConfig(
                    system_instruction=criteria,
                    response_mime_type="application/json",
                    response_json_schema=RESPONSE_SCHEMA,
                ),
            )
            raw = response.text
            try:
                return json.loads(raw)
            except (json.JSONDecodeError, TypeError):
                return {"score": 0, "explanation": str(raw), "verdict": "ERREUR"}

        except errors.APIError as e:
            if e.code in (429, 503) and attempt < retries - 1:
                wait = delay * (attempt + 1)
                print(f"Gemini {e.code}, waiting {wait}s before retry ({attempt + 1}/{retries})...")
                time.sleep(wait)
            else:
                print(f"Gemini error: {e}")
                return {"score": 0, "explanation": str(e), "verdict": "ERREUR"}
        except Exception as e:
            print(f"Gemini error: {e}")
            return {"score": 0, "explanation": str(e), "verdict": "ERREUR"}
