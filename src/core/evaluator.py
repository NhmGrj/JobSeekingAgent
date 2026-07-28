from mistralai.client import Mistral
import os
import json
import time

_client = None


def _get_client() -> Mistral:
    global _client
    if _client is None:
        _client = Mistral(api_key=os.getenv("MISTRAL_API_KEY"))
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
            response = _get_client().chat.complete(
                model="mistral-small-latest",
                messages=[
                    {"role": "system", "content": criteria},
                    {"role": "user", "content": prompt}
                ]
            )
            raw = response.choices[0].message.content
            try:
                clean = raw.replace("```json", "").replace("```", "").strip()
                return json.loads(clean)
            except:
                return {"score": 0, "explanation": raw, "verdict": "ERREUR"}

        except Exception as e:
            if "429" in str(e) and attempt < retries - 1:
                wait = delay * (attempt + 1)
                print(f"Rate limit hit, waiting {wait}s before retry ({attempt + 1}/{retries})...")
                time.sleep(wait)
            else:
                print(f"Mistral error: {e}")
                return {"score": 0, "explanation": str(e), "verdict": "ERREUR"}
