# OpenDash France 🇫🇷

**Dashboard web modulaire qui agrège des dizaines d'API publiques françaises.**
L'utilisateur choisit quels widgets de données afficher, les organise par
glisser-déposer, et tout fonctionne **sans aucune clé API**.

> Cherchez une ville → cochez des widgets (météo, carburants, population…) →
> votre tableau de bord se construit tout seul.

![Capture — vue d'ensemble](docs/screenshot-dashboard.png)
*(placeholder — ajoutez vos captures dans `docs/`)*

---

## ✨ Principes

- **Registre de sources extensible** : chaque source est un objet de config
  (`backend/registry/sources.py`), pas du code en dur dans l'UI.
  Ajouter une source = ajouter un objet (voir [Ajouter une source](#-ajouter-une-source-en-5-min)).
- **Frontend agnostique** : 5 types de rendu (`carte`, `graphe`, `liste`,
  `stat`, `tableau`) = 5 renderers JS génériques. Aucune ligne de front à
  toucher pour une nouvelle source.
- **100 % keyless** : toutes les sources livrées fonctionnent sans clé. Les
  sources futures de type `key` sont simplement grisées tant que la clé manque.
- **Robuste** : si une source tombe, son widget affiche « indisponible » sans
  casser le reste du dashboard.
- **Cache SQLite** avec TTL par source pour limiter les appels réseau.

---

## 🗂 Sources disponibles

| Source | Thème | Rendu | Accès | TTL | Attribution / Licence |
|--------|-------|-------|-------|-----|-----------------------|
| Base Adresse Nationale *(socle, pas un widget)* | — | — | 🟢 keyless | — | BAN (Etalab/DINUM) — Licence Ouverte 2.0 |
| Fiche commune (population) | société | stat | 🟢 keyless | 30 j | API Géo (Etalab/DINUM) — Licence Ouverte 2.0 |
| Météo (Open-Meteo) | météo | graphe | 🟢 keyless | 30 min | Open-Meteo.com — CC BY 4.0 |
| Qualité de l'air | météo | stat | 🟢 keyless | 30 min | Open-Meteo.com (CAMS) — CC BY 4.0 |
| Prix des carburants | énergie | carte | 🟢 keyless | 10 min | Min. Économie / prix-carburants.gouv.fr — Licence Ouverte |
| Hydrométrie (Hub'Eau) | eau | carte | 🟢 keyless | 30 min | Hub'Eau / Eaufrance — Licence Ouverte |
| Recherche d'entreprises | société | liste | 🟢 keyless | 1 h | recherche-entreprises.api.gouv.fr — Licence Ouverte |
| Jours fériés | société | liste | 🟢 keyless | 24 h | calendrier.api.gouv.fr — Licence Ouverte |
| Open Food Facts | alimentation | tableau | 🟢 keyless | 24 h | Open Food Facts — ODbL |
| Prix immobilier (DVF) | immobilier | stat | 🟢 keyless | 24 j | DVF (Etalab/DGFiP) via Opendatasoft — Licence Ouverte |

> **10 sources livrées, toutes keyless.** Les 5 types de rendu sont couverts
> (stat, graphe, carte, liste, tableau). Voir la [roadmap](#-roadmap) pour la suite.

---

## 🚀 Installation

Prérequis : **Python 3.10+**.

```bash
git clone https://github.com/<vous>/opendashfrance.git
cd opendashfrance

python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS / Linux
source .venv/bin/activate

pip install -r requirements.txt
```

(Optionnel) Copier le modèle d'environnement — **non requis**, tout marche sans :

```bash
cp .env.example .env
```

## ▶️ Lancement

```bash
python -m backend.app
```

Puis ouvrir **http://127.0.0.1:5000**.

1. Tapez une **ville ou un code postal** dans la barre de recherche
   (géocodage via la Base Adresse Nationale).
2. Cliquez sur **+ Widgets** et cochez les sources voulues.
3. Réorganisez les tuiles par **glisser-déposer**. La sélection et la
   localisation sont sauvegardées (localStorage).

---

## 🏗 Architecture

```
opendashfrance/
├── backend/
│   ├── app.py              # Flask : /api/sources, /api/geocode, /api/data/<id>
│   ├── config.py           # lecture .env, clés API optionnelles
│   ├── cache.py            # cache SQLite + TTL
│   ├── fetcher.py          # cache → HTTP → parse → enveloppe (gestion d'erreur)
│   ├── geocode.py          # Base Adresse Nationale (socle)
│   └── registry/
│       ├── base.py         # dataclass Source + Context + enveloppe()
│       ├── factories.py    # opendatasoft_source(...) (pattern ODS générique)
│       ├── sources.py      # LE CATALOGUE (objets Source + parsers)
│       └── __init__.py     # REGISTRY = {id: Source}
├── frontend/
│   ├── index.html
│   ├── css/style.css       # dark mode, grille responsive
│   └── js/
│       ├── app.js          # point d'entrée
│       ├── api.js          # client backend
│       ├── state.js        # état + localStorage
│       ├── search.js       # recherche → géocodage
│       ├── gallery.js      # galerie de widgets par thème
│       ├── dashboard.js    # grille + drag & drop
│       └── widgets/        # 1 renderer par type de rendu
├── tests/                  # pytest (parsers, cache, fetcher) — zéro réseau
└── .github/workflows/ci.yml
```

### Format d'échange normalisé

Tout parser renvoie une **enveloppe** commune ; le front choisit le renderer
selon `rendu` :

```json
{ "rendu": "stat", "titre": "Commune de Lyon",
  "data": { "valeur": 522969, "unite": "habitants", "label": "INSEE 69123" } }
```

| `rendu` | forme de `data` |
|---------|-----------------|
| `stat` | `{valeur, unite, label}` |
| `graphe` | `{type:"line\|bar", labels:[], series:[{nom, points:[]}]}` |
| `carte` | `{centre:[lat,lon], markers:[{lat,lon,popup}], geojson?}` |
| `liste` | `{items:[{titre, sous_titre?, valeur?}]}` |
| `tableau` | `{colonnes:[], lignes:[[]]}` |

---

## ➕ Ajouter une source en 5 min

Tout se passe dans `backend/registry/sources.py`. Exemple complet — les
**jours fériés** (rendu `liste`, non géolocalisé) :

```python
from .base import Context, Source, enveloppe


def _jours_feries_url(ctx: Context) -> str:
    # Source nationale, pas besoin du contexte géo.
    return "https://calendrier.api.gouv.fr/jours-feries/metropole.json"


def parse_jours_feries(payload) -> dict:
    # payload = {"2026-01-01": "Jour de l'an", ...}
    items = [{"titre": nom, "sous_titre": date} for date, nom in payload.items()]
    return enveloppe(rendu="liste", titre="Jours fériés", data={"items": items})


source_jours_feries = Source(
    id="jours-feries",
    nom="Jours fériés",
    theme="société",
    acces="keyless",
    besoin_geo=False,
    rendu="liste",
    ttl=24 * 3600,
    attribution="api.gouv.fr — Licence Ouverte",
    description="Jours fériés de l'année en métropole.",
    build_url=_jours_feries_url,
    parse=parse_jours_feries,
)

# … puis l'ajouter à la liste SOURCES :
SOURCES = [source_geo_commune, source_meteo, source_carburants, source_jours_feries]
```

**Pour un portail Opendatasoft** (data.economie.gouv.fr, ADEME, villes…),
utilisez la factory — un seul appel suffit :

```python
from .factories import opendatasoft_source

ma_source = opendatasoft_source(
    id="...", nom="...", theme="...",
    domain="data.economie.gouv.fr",
    dataset_id="<id-du-dataset>",
    rendu="carte", parse=mon_parser, ttl=600,
    attribution="...",
    geo_field="geom",   # filtre par distance autour de lat/lon si fourni
)
```

Ajoutez enfin une **fixture** + un **test** du parser dans `tests/`. C'est tout :
**aucune ligne de frontend à écrire**.

---

## 🧪 Tests & qualité

```bash
ruff check .     # lint
pytest -q        # tests (parsers, cache, fetcher) — 100 % hors-ligne
```

Les tests mockent les réponses HTTP (fixtures dans `tests/fixtures/`,
`responses` pour le réseau) : **aucun appel réseau réel**. GitHub Actions
exécute `ruff` + `pytest` à chaque push (`.github/workflows/ci.yml`).

---

## 🔑 Clés API (optionnelles)

Le dashboard fonctionne **sans `.env`**. Pour activer une future source `key` :
copiez `.env.example` en `.env` et renseignez la variable indiquée. Tant que la
clé manque, la source apparaît grisée (🔒) dans la galerie.

---

## 🗺 Roadmap

- [x] Qualité de l'air (Open-Meteo Air Quality)
- [x] Hub'Eau hydrométrie (stations des cours d'eau proches)
- [x] Recherche d'entreprises (recherche-entreprises.api.gouv.fr)
- [x] Jours fériés (calendrier.api.gouv.fr)
- [x] Open Food Facts (Nutri-Score des produits populaires)
- [x] DVF immobilier (prix médian au m² par localisation)
- [ ] Niveau d'eau temps réel des stations Hub'Eau (pas que le référentiel)
- [ ] Recherche produit OFF par mot-clé (champ de saisie par widget)
- [ ] Contour de commune sur carte (GeoJSON)
- [ ] Profils de dashboard sauvegardés côté backend (SQLite)
- [ ] Export / partage de configuration

---

## 📄 Licence

[MIT](LICENSE). Les données restent soumises aux licences de leurs producteurs
(voir colonne *Attribution* du tableau des sources).
