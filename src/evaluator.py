from mistralai.client import Mistral
from dotenv import load_dotenv
import os
import json
import time

load_dotenv()

client = Mistral(api_key=os.getenv("MISTRAL_API_KEY"))

CRITERIA = """
Tu es un assistant spécialisé dans la recherche d'emploi. Tu dois évaluer des offres d'emploi pour un candidat avec le profil suivant :

- 4 ans d'expérience en Product Management
- Recherche un poste de Product Manager (PM fortement préféré, Product Owner acceptable)
- Localisation : Paris uniquement, ou télétravail total
- Contrat : CDI uniquement
- Salaire minimum : 50 000€ brut annuel
- Expérience principale en B2B, intéressé par le B2C
- Télétravail fréquent ou total fortement préféré, occasionnel acceptable, pas de télétravail = malus mais pas éliminatoire

Pour chaque offre, tu dois retourner :
1. Un score de 1 à 10
2. Une courte explication (2-3 phrases max) des points positifs et négatifs
3. Un verdict : POSTULER, PEUT-ÊTRE, ou IGNORER

Réponds uniquement en JSON avec ce format :
{
  "score": 8,
  "explanation": "...",
  "verdict": "POSTULER"
}
"""

def evaluate_job(job: dict, retries: int = 3, delay: int = 10) -> dict:
    prompt = f"""
Voici une offre d'emploi :
- Titre : {job['title']}
- Entreprise : {job['company']}
- Localisation : {job['location']}
- Contrat : {job['contract']}
- Télétravail : {job['remote']}
- URL : {job['url']}

Évalue cette offre selon les critères fournis.
"""

    for attempt in range(retries):
        try:
            response = client.chat.complete(
                model="mistral-small-latest",
                messages=[
                    {"role": "system", "content": CRITERIA},
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