# Chantiers — multi-plateformes

Objectif : chercher des offres ailleurs que sur WTTJ, sur deux fronts :
- **CDI** (partie A) : chantiers 0 à 2.
- **Freelance** (partie B) : chantiers 3 et 4.

Indeed et LinkedIn sont mis de côté.

# Partie A — CDI

Repérage fait le 2026-10-25 :

| Plateforme | Accès automatisé | Voie retenue |
|---|---|---|
| France Travail | API officielle gratuite | Chantier 1 : API |
| APEC | Bloqué : 403 sur les navigateurs automatisés, même avec un user agent normal | Chantier 2 : alertes e-mail |
| Hellowork | Techniquement facile, mais `robots.txt` interdit `/fr-fr/emploi/recherche.html` aux robots | Chantier 2 : alertes e-mail |

On ne contourne pas les protections anti-robot et on respecte `robots.txt`. Quand un site ferme l'accès automatisé, on passe par ses alertes e-mail.

Ordre dans la partie A : **1 → 2** (voir l'ordre global en fin de fichier). Le chantier 0 est mis de côté jusqu'à ce que deux plateformes alimentent réellement l'agent. D'ici là, une offre présente sur deux plateformes peut arriver en double. Chaque chantier se termine par un vrai run en CI et une entrée dans `JOURNAL.md`.

---

## Chantier 0 — Anti-doublons commun (mis de côté)

> **Mis de côté (2026-10-25).** À reprendre quand deux plateformes alimenteront réellement l'agent. Le point 5 (sources sans navigateur) n'attend pas : il est déplacé dans le chantier 1, qui en a besoin.

**Pourquoi.** Une même offre peut sortir sur WTTJ, France Travail et dans une alerte APEC. Aujourd'hui, la dédup est faite par source (`user_id, source_id, item_key`) : tu la recevrais deux ou trois fois, et Gemini l'évaluerait deux ou trois fois.

**Ce qu'il faut faire**
1. Ajouter un `dedup_group` à `SourceConfig`, par exemple `"jobs"` pour toutes les sources d'emploi. La valeur par défaut est l'`id` de la source, pour ne rien changer aux autres sujets.
2. Utiliser `dedup_group` à la place de `source_id` dans `is_seen` / `mark_seen`. Migration idempotente des lignes existantes (`wttj_jobs` → `jobs`).
3. Clé commune `titre|entreprise` normalisée entre plateformes : minuscules, suppression des accents, de « H/F », « F/H », « (H/F/X) », de la ponctuation et des espaces multiples.
4. Dédupliquer aussi à l'intérieur d'un même run : WTTJ renvoie parfois deux fois la même carte.
5. ~~Contrat `SourceDef` pour les sources sans navigateur~~ : déplacé dans le chantier 1.

**Décisions à prendre**
- Normalisation plus agressive ? Par exemple « Product Manager Senior » = « Senior Product Manager ». Proposition : non au départ, on verra à l'usage.
- Garder une requête Gemini par source ou les regrouper toutes ? Une par source = 3 requêtes/jour sur 20, c'est OK. Une seule = moins de quota, mais une erreur bloque tout.

**Vérification.** Tests locaux de la normalisation sur les titres réels de `seen_jobs.db`, et vérifier que la migration ne fait réévaluer aucune offre déjà vue.

**Taille.** Petite.

---

## Chantier 1 — France Travail (API officielle)

**Pourquoi.** C'est la seule voie 100 % officielle : pas de scraping, pas de risque de blocage, gratuite. France Travail agrège aussi des offres de sites partenaires, donc ça pourrait couvrir une partie de l'APEC et de Hellowork (à vérifier).

**À faire de ton côté**
1. Créer un compte sur francetravail.io, déclarer une application et l'abonner à l'API « Offres d'emploi v2 ».
2. Récupérer le `client_id` et le `client_secret`, et les ajouter en secrets GitHub : `FT_CLIENT_ID`, `FT_CLIENT_SECRET`.

**À faire dans le code**
0. Contrat `SourceDef` : permettre une source sans navigateur (API, e-mail). `page` devient optionnel, et `main.py` n'ouvre un contexte Playwright que si la source en a besoin. Servira aussi au chantier 2.

Dans `src/sources/francetravail_jobs.py` :

1. `login` : obtenir un jeton OAuth (client credentials) sur le serveur d'authentification de France Travail.
2. `scrape` : appeler `GET https://api.francetravail.io/partenaire/offresdemploi/v2/offres/search` avec les filtres mots-clés « product manager » / « product owner », Paris (département 75) et CDI.
3. Faire correspondre les champs de l'API au format commun : titre, entreprise, lieu, contrat, salaire, télétravail si disponible, URL.
4. Ajouter l'entrée dans `config.py` et les secrets dans le workflow.

**À vérifier dans la doc officielle avant de coder.** Les noms exacts des paramètres (mots-clés, département, type de contrat), le scope OAuth, les limites de requêtes, et la présence ou non du télétravail dans les données. Les infos trouvées pour l'instant viennent de sources tierces.

**Risques.** Le volume d'offres PM est peut-être plus faible que sur WTTJ, et les intitulés plus génériques. À juger après le premier run.

**Taille.** Moyenne.

---

## Chantier 2 — Alertes e-mail (APEC, Hellowork)

**Pourquoi.** L'APEC et Hellowork ferment l'accès automatisé à leur recherche, mais proposent des alertes par e-mail. Lire tes propres e-mails est légitime et stable. Le même mécanisme pourra servir plus tard à d'autres sites qui envoient des alertes.

**À faire de ton côté**
1. Créer une **adresse Gmail dédiée** aux alertes (recommandé : l'agent n'a alors pas accès à ta boîte perso).
2. Sur cette adresse : activer la validation en 2 étapes, puis créer un « mot de passe d'application » pour l'accès IMAP.
3. Créer les alertes APEC et Hellowork vers cette adresse : product manager / product owner, Paris + télétravail, CDI.
4. Secrets GitHub : `ALERTS_EMAIL`, `ALERTS_APP_PASSWORD`.

**À faire dans le code**
1. Une source générique `src/sources/email_alerts.py` : connexion IMAP, lecture des e-mails non lus par expéditeur, puis marquage comme lus (ou déplacement dans un libellé « traité »).
2. Un analyseur HTML par expéditeur (`apec`, `hellowork`) qui extrait titre, entreprise, lieu, contrat, salaire si présent, et lien.
3. Si un e-mail d'un expéditeur connu ne donne aucune offre, lever une erreur pour recevoir le ⚠️ sur Telegram : c'est le signe que le format de l'e-mail a changé.
4. Ajouter l'entrée dans `config.py`.

**Avant de coder.** Attendre de recevoir 2 ou 3 vrais e-mails d'alerte de chaque site pour écrire les analyseurs sur leur vrai format.

**Risques**
- Les e-mails d'alerte contiennent souvent moins d'infos que l'offre complète (pas toujours le télétravail). Gemini jugera avec moins d'éléments.
- Si un site change le format de ses e-mails, son analyseur cesse de fonctionner. Le point 3 ci-dessus sert à le détecter.

**Taille.** Moyenne à grande : deux analyseurs, plus l'IMAP.

---

# Partie B — Freelance

Le sujet `"freelance"` existe déjà dans le code (libellé Telegram « 🧑‍💻 Freelance »).

Repérage fait le 2026-10-26 :

| Plateforme | Fonctionnement | Accès automatisé | Voie retenue |
|---|---|---|---|
| Free-Work | Job board public de missions freelance IT, avec des missions PM/PO | `robots.txt` autorise la recherche ; la page de recherche se charge (HTTP 200, ~70 missions) | Chantier 3 : scraping |
| Malt | Le client te contacte via ton profil, peu de missions publiques | `robots.txt` non récupérable (à revérifier) | Chantier 4 : notifications e-mail |
| Comet, Crème de la Crème, Collective | Plateformes sélectives : missions proposées dans l'espace connecté et par e-mail | Pas d'annuaire public de missions | Chantier 4 : notifications e-mail |

## Critères freelance (fixés le 2026-10-26)

- **Rôle :** Product Manager / Product Owner, ainsi que Technical PM, Product Analyst / PO. Profil généraliste : le Cloud n'est pas un filtre.
- **Bonus :** B2B / SaaS, Cloud / IaaS / infra, IA / LLM / agents, rôle avec une composante technique.
- **TJM (HT) :** plancher 500 €, cible 600 – 650 €. Au-dessus de 700 €, c'est très bien. Si le TJM n'est pas indiqué, ne pas écarter l'offre. (Le TJM affiché sur tes profils est de 650 € HT. C'est une info pour tes profils Malt & co, pas un critère d'évaluation.)
- **Intermédiaires :** ESN, cabinets et plateformes acceptés.
- **Lieu :** Paris ou télétravail. Toutes les formules sont acceptées : sur site, hybride, full remote.
- **Durée :** pas de minimum.
- **Démarrage :** dès que possible.
- **Temps :** plein ou partiel.
- **Expérience demandée :** ne pas écarter une annonce qui demande « 5 – 10 ans » ou plus.
- **Rôles à écarter :** aucun pour l'instant.

Ces critères deviendront le `default_criteria` des sources freelance (chantiers 3 et 4). Le texte est en anglais, comme le reste du code, et calqué sur `src/sources/wttj_jobs.py` :

```
You are an assistant specialized in freelance job hunting. You evaluate freelance missions for a candidate with the following profile:

- 4 years of experience in Product Management
- Looking for a Product Manager or Product Owner mission (also: Technical PM, Product Analyst / PO). Generalist profile: cloud experience is not a requirement
- Bonus: B2B / SaaS, Cloud / IaaS / infrastructure, AI / LLM / agents, roles with a technical component
- Daily rate (excl. VAT): minimum €500, target €600-650, above €700 is excellent. If the daily rate is not stated, do not penalize the mission
- Missions through IT services firms (ESN), consulting firms or platforms are fine
- Location: Paris or remote; on-site, hybrid and fully remote are all acceptable
- No minimum duration; full-time or part-time both acceptable; can start immediately
- Do not penalize a mission that asks for 5-10+ years of experience

For each mission, return:
1. A score from 1 to 10
2. A short explanation (2-3 sentences max) of the pros and cons
3. A verdict: APPLY, MAYBE, or SKIP
```

## Chantier 3 — Free-Work (scraping)

**Pourquoi.** C'est la seule grosse plateforme freelance avec un annuaire public de missions qui autorise l'accès automatisé à sa recherche.

**À faire dans le code** (`src/sources/freework_freelance.py`, sujet `"freelance"`)
1. Trouver l'URL de recherche qui filtre vraiment « product manager / product owner », freelance, Paris ou remote. Le premier essai (`?query=product%20manager&contracts=contractor`) ne filtrait pas : les résultats étaient génériques.
2. `scrape` : lire les cartes de mission (titre, client ou ESN, lieu, TJM si affiché, durée, télétravail, lien) et gérer la pagination. Pas de `login` : la recherche est publique.
3. Si la recherche renvoie 0 mission, lever une erreur pour recevoir le ⚠️ Telegram. C'est le signe que la page a changé.
4. Ajouter l'entrée dans `config.py` avec les critères freelance.

**Risques.** Beaucoup de missions passent par des ESN ou des intermédiaires, souvent en doublon de la même mission. Le TJM n'est pas toujours affiché.

**Taille.** Moyenne. C'est le même type de travail que WTTJ, sans connexion.

## Chantier 4 — Notifications e-mail freelance (Malt, Comet, Crème de la Crème, Collective)

**Pourquoi.** Ces plateformes n'ont pas d'annuaire public : les missions arrivent par e-mail une fois ton profil créé et validé. On réutilise **le mécanisme du chantier 2** (lecture IMAP d'une boîte Gmail dédiée), avec un analyseur par expéditeur.

**Prérequis**
- Chantier 2 fait : la source e-mail générique existe.
- Ton profil créé ou validé sur chaque plateforme, avec les notifications e-mail envoyées vers l'adresse dédiée (ou redirigées vers elle).
- 2 ou 3 vrais e-mails de chaque plateforme avant d'écrire les analyseurs.

**À faire dans le code.** Un analyseur HTML par expéditeur dans la source e-mail, avec sujet `"freelance"` et les critères freelance.

**Risques**
- Certaines notifications ne contiennent qu'un teaser (« une nouvelle mission correspond à ton profil ») sans le détail. Dans ce cas, l'analyseur ne récupère que le titre et le lien, et Gemini juge sur peu d'éléments.
- Le rythme d'envoi dépend de chaque plateforme.

**Taille.** Petite par plateforme une fois le chantier 2 fait.

---

## Ordre global proposé
1. **Chantier 1** — France Travail (CDI)
2. **Chantier 3** — Free-Work (freelance) : indépendant du reste, peut se faire avant ou en parallèle du chantier 1.
3. **Chantier 0** — Anti-doublons, dès que deux plateformes tournent.
4. **Chantier 2** — Source e-mail + APEC / Hellowork (CDI)
5. **Chantier 4** — Notifications freelance, sur la base du chantier 2.

## Hors périmètre pour l'instant
- Indeed, LinkedIn : mis de côté. Leurs alertes e-mail pourraient se brancher sur le chantier 2 plus tard, si tu changes d'avis.
- Fusion des offres en double entre plateformes dans le rapport (afficher « vue sur WTTJ + APEC ») : à voir après le chantier 0.
