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

## 2026-07-28 — Refonte multi-utilisateurs / multi-sources

### Pourquoi
Le projet était mono-tenant : un seul compte WTTJ, un seul profil d'évaluation (PM), une seule destination Telegram, une dédup indexée uniquement sur `title|company`. Objectif : préparer le terrain pour plusieurs utilisateurs (chacun avec ses propres identifiants et sa propre destination Telegram), chacun pouvant faire tourner plusieurs "sources" (plateforme + sujet, ex: "WTTJ jobs" ou "Bien'ici appartements"), sans devoir tout réécrire au moment d'ajouter la 2e source réelle. Portée volontairement limitée : architecture seulement, pas de nouveau scraper fonctionnel (Bien'ici = stub `NotImplementedError`), Notion débranché du flux actif (le fichier reste, juste plus appelé — l'utilisateur ne l'utilise pas).

### Nouvelle structure
```
src/
  config.py                    # UserConfig/SourceConfig, validate_config(), registre USERS
  sources/
    base.py                    # contrat SourceDef (login/scrape/item_key/format_summary)
    wttj_jobs.py                # ex scraper.py, migré derrière le contrat
    bienici_apartments.py       # stub NotImplementedError, non branché dans USERS
  core/
    database.py                 # ex database.py, dédup généralisée
    evaluator.py                 # ex evaluator.py, critères paramétrables
    reporter_telegram.py         # ex reporter.py, chat_id/token en paramètres
    reporter_notion.py           # ex notion_reporter.py, déplacé, plus appelé
    results_writer.py            # extraction de l'écriture markdown
  main.py                       # boucle sur USERS → sources, au lieu du flux unique d'avant
```
Déplacements faits via `git mv` pour préserver l'historique.

### Dédup : correction d'une collision silencieuse
L'ancienne clé (`title|company` seul) aurait fait collision entre deux sources/utilisateurs différents scrapant une offre avec le même titre+entreprise. Nouvelle table `seen_items`, clé composite `(user_id, source_id, item_key)`. Migration automatique et idempotente au premier démarrage : les 289 lignes de l'ancienne table `seen_jobs` sont recopiées avec `user_id='nhm', source_id='wttj_jobs'` — testé sur une copie de la vraie base (289 lignes migrées, ré-exécution sans doublon). L'ancienne table `seen_jobs` est laissée en place intacte, par sécurité.

### Bug corrigé au passage
`main.py` écrivait son rapport markdown à la racine du repo (`../results_<date>.md`) au lieu du dossier `results/` que la CI crée et upload comme artefact — cet artefact était donc vide depuis le début. `results_writer.py` écrit maintenant dans `results/<user_id>_<date>.md`.

### Repéré, non corrigé (hors périmètre de cette passe)
`mark_seen()` est appelé même quand Mistral échoue (verdict `ERREUR`), ce qui supprime définitivement toute nouvelle tentative sur un échec transitoire de l'API. Pré-existant, pas introduit par cette refonte.

### CI / secrets
Retrait de `NOTION_TOKEN`/`NOTION_DATABASE_ID` du `env:` du workflow (plus rien ne les lit) et de `.env.example`. Les identifiants WTTJ/Telegram existants n'ont pas été renommés — aucune modification à faire côté secrets GitHub pour que la CI continue de fonctionner à l'identique. Un futur 2e utilisateur/source suit une convention `<USER>_<PLATEFORME>_<CHAMP>` (documentée en commentaire dans `.env.example` et `config.py`).
