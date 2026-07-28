# Journal

## 2026-07-28 — État des lieux, nettoyage, migration Notion

### Ce que fait le projet
Agent qui tourne quotidiennement (GitHub Actions, `.github/workflows/daily_job_hunt.yml`, cron 7h) :
- `src/scraper.py` — se connecte à Welcome to the Jungle (Playwright) et scrape les offres du fil "matches"
- `src/database.py` — SQLite (`seen_jobs.db`) pour dédupliquer les offres déjà vues
- `src/evaluator.py` — évalue chaque nouvelle offre avec Mistral (score /10, verdict POSTULER/PEUT-ÊTRE/IGNORER) sur un profil PM Paris/remote
- `src/reporter.py` — envoie un résumé sur Telegram
- `src/notion_reporter.py` — pousse les offres retenues dans une base Notion
- `src/main.py` — orchestre le tout

### Nettoyage effectué
Suppression de fichiers qui traînaient à la racine, sans rapport avec le code (déjà stagés avant cette entrée) :
- `debug.png`, `main`, `qdsdqsdqsd`, `results_2026-05-29_06-05.md`

### Migration Google Sheets → Notion
- `.env.example` : `GOOGLE_CREDENTIALS`/`GOOGLE_SHEET_ID` remplacés par `NOTION_TOKEN`/`NOTION_DATABASE_ID`
- `requirements.txt` : retrait de `gspread`, `google-auth`, `gspread-formatting`
- Le reporting passe désormais par `notion_reporter.py` plutôt qu'un ancien reporter Google Sheets

### Point relevé (non traité)
`.github/workflows/daily_job_hunt.yml` référence encore `GOOGLE_CREDENTIALS` et `GOOGLE_SHEET_ID` dans les `env:` du job, alors que le code ne les utilise plus. À nettoyer si confirmé obsolète.

## 2026-07-28 — Suppression des secrets Google Sheets du workflow CI

Confirmé : plus aucune référence à `GOOGLE_CREDENTIALS`/`GOOGLE_SHEET_ID`/`gspread` dans le code Python (`grep` sur `*.py`). Retrait des deux lignes correspondantes dans `.github/workflows/daily_job_hunt.yml` (`env:` de l'étape "Run job hunter"). Les secrets GitHub `GOOGLE_CREDENTIALS`/`GOOGLE_SHEET_ID` eux-mêmes restent configurés côté repo GitHub — à supprimer manuellement dans Settings → Secrets si tu veux finir le ménage (je n'ai pas accès à ça depuis ici).
