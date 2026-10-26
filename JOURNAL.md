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

## 2026-10-24 — Login WTTJ cassé depuis le 2026-10-02 (user agent headless bloqué)

### Symptôme
Depuis le run du 2026-10-02, chaque exécution échoue au login : `Page.wait_for_selector: Timeout 30000ms exceeded` sur `[data-testid="sign-in-form-email-input"]`. Aucune offre scrapée depuis. Le workflow restait pourtant vert : l'exception est attrapée dans `main.py` et le `| tee` masquait de toute façon le code de sortie.

### Cause
Le CDN (CloudFront) de WTTJ renvoie maintenant 403 « The request could not be satisfied » au user agent par défaut de Chromium headless (`HeadlessChrome`). Avec un UA Chrome classique, la page se charge normalement. Les sélecteurs du formulaire de login sont inchangés (vérifié avec Playwright).

### Correctifs
- `src/main.py` : `browser.new_context(user_agent=USER_AGENT)` avec un UA Chrome desktop.
- `src/main.py` : `main()` renvoie 1 si une source ou un utilisateur a échoué, pour que le run CI passe en rouge.
- Workflow : `set -o pipefail` pour que `| tee` ne masque plus l'échec. Les étapes commit DB / upload restent en `if: always()`.

## 2026-10-24 — Mistral inutilisable, sauvegarde des offres non évaluées

Le run manuel après le correctif du login a bien scrapé (51 offres, 8 nouvelles uniques), mais Mistral a renvoyé `429 Rate limit exceeded` (code 1300) sur toutes les évaluations, même après les retries. Décision : on abandonne Mistral, migration vers l'API Claude à discuter.

Problème : `main.py` marquait l'offre comme vue même quand l'évaluation échouait (`ERREUR`), donc ces offres n'auraient jamais été réévaluées.
- `src/main.py` : `mark_seen` uniquement si le verdict n'est pas `ERREUR` ; une offre en échec sera retentée au run suivant.
- `seen_jobs.db` : suppression des 8 lignes du run du 2026-10-24 21:30 UTC (Kanbios x2, Linxea, Safran.AI, Health Data Hub, Pelico, Manutan, Dedale) pour qu'elles soient réévaluées.

## 2026-10-24 — Remplacement de Mistral par Gemini (free tier)

Contrainte : rester gratuit. L'API Claude est payante uniquement ; GitHub Models semble retiré (juillet 2026). Choix : Google Gemini, free tier (~10 req/min, ~1 500 req/jour sur les modèles Flash, large pour ~10 offres/jour). Attention : sur le free tier, Google peut utiliser les contenus envoyés pour améliorer ses produits (ici : offres publiques + critères de profil).

- `src/core/evaluator.py` : SDK `google-genai`, modèle `gemini-3.8-flash`, `generate_content` avec `system_instruction` = critères et sortie JSON contrainte par schéma (`response_json_schema`), ce qui supprime les erreurs de parsing. Retry sur 429 conservé (via `errors.APIError.code`).
- `src/main.py` : pause de 7 s entre deux évaluations (au lieu de 3 s) pour rester sous la limite par minute.
- `requirements.txt` : `mistralai` → `google-genai`.
- Workflow + `.env.example` : `MISTRAL_API_KEY` → `GEMINI_API_KEY`.

Testé localement avec une fausse clé : la requête atteint l'API Google et échoue uniquement sur la clé. Reste à créer la clé sur aistudio.google.com et l'ajouter en secret GitHub `GEMINI_API_KEY`.

## 2026-10-25 — Premier run Gemini : 503 et message Telegram rejeté

Run manuel `40146055046` : Gemini fonctionne (8/13 offres évaluées, dont 4 POSTULER). Deux problèmes :
- 5 offres en `503 UNAVAILABLE` (« high demand », surcharge temporaire côté Google). Seul le 429 était retenté. `src/core/evaluator.py` : retry aussi sur 503. Les 5 offres sont restées non vues et seront réévaluées au prochain run.
- 1 message Telegram rejeté (`can't parse entities`) : le mode `Markdown` legacy casse dès qu'une explication contient `_`, `*`, etc. `src/core/reporter_telegram.py` : passage en `parse_mode: HTML` avec `html.escape` sur le résumé, l'URL et l'explication.

## 2026-10-25 — Évaluation en une seule requête + erreurs envoyées sur Telegram

Constat du run `40147132291` : le free tier de `gemini-3.8-flash` est limité à **20 requêtes/jour** (message d'erreur Google, quota `GenerateRequestsPerDayPerProjectPerModel-FreeTier`), pas ~1 500 comme annoncé par des guides tiers. Avec une requête par offre + les retries, le quota a été épuisé en deux runs. Le correctif Telegram HTML a bien fonctionné.

Décision (avec l'utilisateur) :
- `src/core/evaluator.py` : `evaluate_items()` évalue toutes les nouvelles offres d'une source en **une seule requête** (offres numérotées, réponse JSON = liste contrainte par schéma, réordonnée par `index`). Plus de retry ni de pause : toute erreur (API, JSON, offre manquante dans la réponse) est levée telle quelle.
- `src/core/reporter_telegram.py` : `send_error()` envoie sur Telegram le nom de la source, le type d'exception et son message (échappé HTML, tronqué à 3 500 caractères).
- `src/main.py` : toute erreur d'une source (login, scraping ou évaluation) est envoyée sur Telegram, le run passe en échec, et rien n'est marqué vu (réévaluation au run suivant). Pas de message « Rien de nouveau » si la seule nouvelle est une erreur.

Choix volontaire : pas de retry ni de fallback vers un autre modèle pour l'instant. On voit les erreurs arriver sur Telegram, puis on décide.

Testé en local : réponse simulée (ordre mélangé), réponse incomplète, et vraie erreur API (fausse clé). Pas encore de vrai run, quota du jour épuisé.

## 2026-10-26 — Retry Gemini sur 5xx pendant 1 h

Run planifié `40192355975` (2026-10-25) : login et scraping WTTJ OK, mais Gemini a répondu `503 UNAVAILABLE` (« high demand ») et, sans retry depuis le commit précédent, l'erreur est partie directement sur Telegram.

Décision (avec l'utilisateur) : retenter largement les erreurs serveur passagères, et n'alerter que si ça dure.
- `src/core/evaluator.py` : `_generate_with_retry()` retente les codes 500/503/504 avec des pauses de 1, 2, 4, 8 puis 15 min, jusqu'à 1 h après la première tentative (8 tentatives au plus, donc 8 requêtes sur le quota de 20/jour). Au-delà, une `RuntimeError` « Gemini indisponible depuis N min… » est levée : le ⚠️ part sur Telegram, rien n'est marqué vu, on réessaie au run du lendemain. Les autres erreurs (429 quota, clé invalide, JSON…) ne sont pas retentées.
- 1 h plutôt que 2 h : les pics de 503 durent en général quelques minutes. Au-delà d'une heure, c'est plutôt une panne longue, les offres sont de toute façon reprises le lendemain, et 2 h ne ferait que retarder l'alerte.
- Workflow : `timeout-minutes: 120` sur le job (scraping ~15 min + 1 h de retries), en garde-fou.

Testé en local avec un faux client et une fausse horloge : succès après trois 503, abandon à ~61 min après 8 tentatives sur 503 permanent, 429 levé immédiatement.
