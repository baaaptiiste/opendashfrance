# OpenDash France 🇫🇷

**Un tableau de bord web qui réunit plein de données publiques françaises au même endroit.**

Vous tapez une ville, vous cochez les infos qui vous intéressent (météo, prix des
carburants, population, immobilier…), et votre tableau de bord se construit tout
seul. **Aucune inscription, aucune clé API : ça marche directement.**

![Capture — vue d'ensemble](docs/screenshot-dashboard.png)
*(placeholder — ajoutez vos captures d'écran dans le dossier `docs/`)*

---

## 🎯 Comment ça marche, en 3 étapes

1. **Cherchez une ville** (ou un code postal) dans la barre du haut.
2. **Cliquez sur « + Widgets »** et cochez les données que vous voulez voir.
3. **Lisez votre tableau de bord.** Vous pouvez déplacer les tuiles à la souris ;
   votre sélection est mémorisée pour la prochaine visite.

Chaque tuile (= un « widget ») affiche une donnée : un chiffre, un graphique,
une carte, une liste ou un tableau.

---

## 📚 Vocabulaire (si certains mots vous bloquent)

| Mot | Ce que ça veut dire ici |
|-----|--------------------------|
| **API publique** | Un service en ligne qui fournit des données gratuites (ex. la météo). |
| **Widget** | Une tuile du tableau de bord qui affiche une donnée. |
| **Source** | L'origine d'une donnée (une API). Ex. « Météo », « Carburants ». |
| **Keyless** | Source utilisable sans mot de passe ni clé. Toutes les nôtres le sont. |
| **Cache** | On garde les réponses un moment pour ne pas re-télécharger sans arrêt. |
| **TTL** | Durée pendant laquelle une donnée en cache reste valable (ex. 10 min). |

---

## 🗂 Les données disponibles (10 sources)

Toutes gratuites et sans clé. La colonne « Affichage » dit sous quelle forme la
donnée apparaît.

| Donnée | Catégorie | Affichage | Mise à jour | Source / Licence |
|--------|-----------|-----------|-------------|------------------|
| Population de la commune | société | chiffre | 30 jours | API Géo (Etalab) — Licence Ouverte |
| Météo (24 h) | météo | graphique | 30 min | Open-Meteo — CC BY 4.0 |
| Qualité de l'air | météo | chiffre | 30 min | Open-Meteo (CAMS) — CC BY 4.0 |
| Prix des carburants | énergie | carte | 10 min | Min. Économie — Licence Ouverte |
| Cours d'eau proches | eau | carte | 30 min | Hub'Eau / Eaufrance — Licence Ouverte |
| Entreprises locales | société | liste | 1 h | recherche-entreprises.api.gouv.fr — Licence Ouverte |
| Jours fériés | société | liste | 24 h | calendrier.api.gouv.fr — Licence Ouverte |
| Produits & Nutri-Score | alimentation | tableau | 24 h | Open Food Facts — ODbL |
| Prix immobilier (DVF) | immobilier | chiffre | 24 jours | DVF (Etalab/DGFiP) — Licence Ouverte |
| *Recherche d'adresse* | *socle* | *—* | *—* | *Base Adresse Nationale (Etalab)* |

> La « Recherche d'adresse » n'est pas un widget : c'est elle qui transforme
> votre « ville » en coordonnées utilisées par les autres widgets.

**Une source en panne ?** Son widget affiche simplement « indisponible » ; les
autres continuent de fonctionner normalement.

---

## 🚀 Installation

Il faut **Python 3.10 ou plus récent**. Dans un terminal :

```bash
# 1. Récupérer le projet
git clone https://github.com/baaaptiiste/opendashfrance.git
cd opendashfrance

# 2. Créer un environnement Python isolé
python -m venv .venv

# 3. L'activer
.venv\Scripts\activate        # Windows
source .venv/bin/activate     # macOS / Linux

# 4. Installer les dépendances
pip install -r requirements.txt
```

## ▶️ Lancement

```bash
python -m backend.app
```

Ouvrez ensuite **http://127.0.0.1:5000** dans votre navigateur. C'est tout.

> Pas besoin de fichier `.env` : tout fonctionne sans configuration.

---

## 🧠 Comment c'est construit (vue d'ensemble)

- **Le « cerveau » (backend, en Python/Flask)** récupère les données auprès des
  API, les nettoie, les met en cache, et les renvoie dans un format unique.
- **L'interface (frontend, en HTML/CSS/JavaScript)** affiche ces données. Elle ne
  connaît rien aux API : elle sait juste afficher 5 formes (chiffre, graphique,
  carte, liste, tableau).

L'idée clé : **pour ajouter une nouvelle donnée, on ne touche jamais à
l'interface.** On décrit juste la source dans un fichier, et le widget apparaît.

```
opendashfrance/
├── backend/                  # le serveur Python
│   ├── app.py                # les 3 adresses de l'API (voir plus bas)
│   ├── cache.py              # mémoire temporaire (SQLite)
│   ├── fetcher.py            # va chercher la donnée + gère les pannes
│   ├── geocode.py            # transforme "Lyon" en coordonnées
│   └── registry/
│       └── sources.py        # 👈 LE CATALOGUE de toutes les sources
├── frontend/                 # l'interface web
│   ├── index.html
│   ├── css/style.css
│   └── js/                   # dont widgets/ = les 5 façons d'afficher
├── tests/                    # tests automatiques
└── .github/workflows/ci.yml  # vérifications auto sur GitHub
```

### Les 3 adresses de l'API

| Adresse | Rôle |
|---------|------|
| `GET /api/sources` | La liste des données disponibles. |
| `GET /api/geocode?q=Lyon` | Transforme une ville en coordonnées. |
| `GET /api/data/<source>` | Renvoie la donnée d'une source (ex. la météo). |

---

## ➕ Ajouter une nouvelle source

Tout se passe dans un seul fichier : `backend/registry/sources.py`.
Il faut 3 choses : **où chercher** la donnée, **comment la ranger**, et
**l'ajouter au catalogue**. Exemple complet avec les jours fériés :

```python
from .base import Context, Source, enveloppe

# 1) OÙ chercher : l'adresse de l'API à appeler.
def _jours_feries_url(ctx: Context) -> str:
    return "https://calendrier.api.gouv.fr/jours-feries/metropole/2026.json"

# 2) COMMENT ranger : transformer la réponse en format standard.
def parse_jours_feries(payload) -> dict:
    # payload reçu = {"2026-01-01": "Jour de l'an", ...}
    items = [{"titre": nom, "sous_titre": date} for date, nom in payload.items()]
    return enveloppe(rendu="liste", titre="Jours fériés", data={"items": items})

# 3) DÉCRIRE la source (ses réglages).
source_jours_feries = Source(
    id="jours-feries",          # identifiant unique
    nom="Jours fériés",          # nom affiché
    theme="société",             # catégorie dans la galerie
    acces="keyless",             # pas de clé nécessaire
    besoin_geo=False,            # pas besoin d'une ville
    rendu="liste",               # forme d'affichage
    ttl=24 * 3600,               # garder en cache 24 h
    attribution="api.gouv.fr — Licence Ouverte",
    description="Jours fériés de l'année.",
    build_url=_jours_feries_url,
    parse=parse_jours_feries,
)

# 4) L'ajouter à la liste SOURCES (tout en bas du fichier).
```

**Astuce :** beaucoup de portails publics (économie, ADEME, villes…) utilisent le
même moteur « Opendatasoft ». Pour ceux-là, une fonction raccourci existe :

```python
from .factories import opendatasoft_source

ma_source = opendatasoft_source(
    id="...", nom="...", theme="...",
    domain="data.economie.gouv.fr",   # le portail
    dataset_id="<id-du-jeu-de-donnees>",
    rendu="carte", parse=mon_parser, ttl=600,
    attribution="...",
    geo_field="geom",   # pour filtrer autour de la ville cherchée
)
```

C'est fini : **aucune ligne d'interface à écrire**, le widget apparaît tout seul.
(Pensez quand même à ajouter un petit test, voir ci-dessous.)

---

## 🧪 Lancer les tests

```bash
ruff check .     # vérifie le style du code
pytest -q        # lance les tests
```

Les tests utilisent des réponses d'API enregistrées à l'avance (dans
`tests/fixtures/`) : **ils ne vont jamais sur Internet**, donc ils sont rapides
et fiables. GitHub les relance automatiquement à chaque envoi de code.

---

## 🔑 Clés API (pour plus tard, optionnel)

Toutes les sources actuelles marchent sans clé. Si un jour on ajoute une source
qui en demande une, il suffira de copier `.env.example` en `.env` et d'y mettre
la clé. Tant qu'elle manque, la source apparaît grisée (🔒) — le reste continue
de marcher.

---

## 🗺 La suite (roadmap)

Déjà fait ✅

- [x] Qualité de l'air, hydrométrie, entreprises, jours fériés, Nutri-Score, immobilier

À venir 🔜

- [ ] Niveau d'eau en temps réel des cours d'eau
- [ ] Recherche d'un produit alimentaire par mot-clé
- [ ] Contour de la commune sur la carte
- [ ] Sauvegarde de plusieurs tableaux de bord
- [ ] Export / partage de configuration

---

## 📄 Licence

Code sous licence [MIT](LICENSE) — réutilisable librement.
Les **données** restent soumises aux licences de leurs fournisseurs (voir la
colonne « Source / Licence » du tableau plus haut).
