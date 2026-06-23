"""Catalogue des sources de données.

Chaque source = un objet ``Source`` ajouté à ``SOURCES``. Les fonctions
``parse_*`` sont volontairement PURES (entrée = JSON brut de l'API, sortie =
enveloppe normalisée) : zéro I/O, donc faciles à tester avec des fixtures
mockées (voir tests/test_parsers.py).

--- AJOUTER UNE SOURCE EN 5 MIN ---
1. Écrire une fonction ``parse_xxx(payload) -> enveloppe(...)``.
2. Créer un ``Source(...)`` (ou ``opendatasoft_source(...)`` pour un portail ODS).
3. L'ajouter à la liste ``SOURCES`` ci-dessous.
4. Ajouter une fixture + un test du parser.
C'est tout : aucune ligne de frontend à toucher.
"""

from __future__ import annotations

import datetime
import statistics
from urllib.parse import urlencode

from .base import Context, Source, enveloppe
from .factories import opendatasoft_source

# ---------------------------------------------------------------------------
# 1) Fiche commune — API Geo découpage administratif (geo.api.gouv.fr)
#    Rendu : stat (population). Géolocalisé via code INSEE.
# ---------------------------------------------------------------------------

GEO_FIELDS = "nom,code,population,centre"


def _geo_commune_url(ctx: Context) -> str:
    params = {"fields": GEO_FIELDS, "format": "json"}
    if ctx.code_insee:
        params["code"] = ctx.code_insee
    elif ctx.lat is not None and ctx.lon is not None:
        # Repli : commune contenant le point.
        params["lat"] = ctx.lat
        params["lon"] = ctx.lon
    return f"https://geo.api.gouv.fr/communes?{urlencode(params)}"


def parse_geo_commune(payload) -> dict:
    """payload = liste de communes ; on prend la première."""
    if not payload:
        raise ValueError("Aucune commune trouvée")
    commune = payload[0] if isinstance(payload, list) else payload
    pop = commune.get("population")
    return enveloppe(
        rendu="stat",
        titre=f"Commune de {commune.get('nom', '?')}",
        data={
            "valeur": pop,
            "unite": "habitants",
            "label": f"INSEE {commune.get('code', '?')}",
        },
    )


source_geo_commune = Source(
    id="geo-commune",
    nom="Fiche commune",
    theme="société",
    acces="keyless",
    besoin_geo=True,
    rendu="stat",
    ttl=30 * 24 * 3600,  # données administratives : ~30 jours
    attribution="API Géo (Etalab/DINUM) — Licence Ouverte 2.0",
    description="Population de la commune sélectionnée (découpage administratif).",
    build_url=_geo_commune_url,
    parse=parse_geo_commune,
)


# ---------------------------------------------------------------------------
# 2) Météo — Open-Meteo (api.open-meteo.com)
#    Rendu : graphe (température horaire sur 24 h). Géolocalisé via lat/lon.
# ---------------------------------------------------------------------------


def _meteo_url(ctx: Context) -> str:
    params = {
        "latitude": ctx.lat if ctx.lat is not None else 48.8566,
        "longitude": ctx.lon if ctx.lon is not None else 2.3522,
        "hourly": "temperature_2m",
        "forecast_days": 1,
        "timezone": "auto",
    }
    return f"https://api.open-meteo.com/v1/forecast?{urlencode(params)}"


def parse_meteo(payload) -> dict:
    hourly = payload.get("hourly", {})
    times = hourly.get("time", [])
    temps = hourly.get("temperature_2m", [])
    unite = payload.get("hourly_units", {}).get("temperature_2m", "°C")
    # Garde uniquement HH:MM pour des labels lisibles.
    labels = [t.split("T")[-1] for t in times]
    return enveloppe(
        rendu="graphe",
        titre="Température (24 h)",
        data={
            "type": "line",
            "labels": labels,
            "series": [{"nom": f"Température ({unite})", "points": temps}],
        },
    )


source_meteo = Source(
    id="meteo",
    nom="Météo (Open-Meteo)",
    theme="météo",
    acces="keyless",
    besoin_geo=True,
    rendu="graphe",
    ttl=30 * 60,  # 30 min
    attribution="Open-Meteo.com — CC BY 4.0",
    description="Prévision de température horaire sur les prochaines 24 heures.",
    build_url=_meteo_url,
    parse=parse_meteo,
)


# ---------------------------------------------------------------------------
# 3) Prix carburants — Opendatasoft (data.economie.gouv.fr)
#    Rendu : carte (stations + prix). Géolocalisé via lat/lon (distance ODS).
# ---------------------------------------------------------------------------


def parse_carburants(payload) -> dict:
    """Normalise les enregistrements ODS en marqueurs de carte.

    Chaque résultat = une station. On lit les coordonnées depuis le champ géo
    ``geom`` (geo_point_2d ODS, sérialisé {"lon":..., "lat":...}) et on agrège
    les prix présents (clés se terminant par ``_prix``) dans le popup.
    """
    results = payload.get("results", [])
    markers = []
    centre = None
    for r in results:
        geom = r.get("geom") or {}
        lat = geom.get("lat")
        lon = geom.get("lon")
        if lat is None or lon is None:
            continue
        if centre is None:
            centre = [lat, lon]
        # Récupère tous les prix disponibles pour la station.
        prix = {
            k.replace("_prix", "").upper(): v
            for k, v in r.items()
            if k.endswith("_prix") and v is not None
        }
        prix_txt = ", ".join(f"{nom} {val} €" for nom, val in prix.items()) or "n.c."
        adresse = r.get("adresse", "")
        ville = r.get("ville", "")
        markers.append(
            {
                "lat": lat,
                "lon": lon,
                "popup": f"<b>{ville}</b><br>{adresse}<br>{prix_txt}",
            }
        )
    return enveloppe(
        rendu="carte",
        titre="Prix des carburants à proximité",
        data={"centre": centre, "markers": markers},
    )


source_carburants = opendatasoft_source(
    id="carburants",
    nom="Prix des carburants",
    theme="énergie",
    domain="data.economie.gouv.fr",
    dataset_id="prix-des-carburants-en-france-flux-instantane-v2",
    rendu="carte",
    parse=parse_carburants,
    ttl=10 * 60,  # 10 min (prix volatils)
    attribution="Ministère de l'Économie — prix-carburants.gouv.fr / Licence Ouverte",
    description="Stations-service proches et leurs prix instantanés.",
    geo_field="geom",
    rayon_m=5000,
    limit=50,
)


# ---------------------------------------------------------------------------
# 4) Qualité de l'air — Open-Meteo Air Quality
#    Rendu : stat (indice AQI européen courant). Géolocalisé via lat/lon.
# ---------------------------------------------------------------------------


def _air_url(ctx: Context) -> str:
    params = {
        "latitude": ctx.lat if ctx.lat is not None else 48.8566,
        "longitude": ctx.lon if ctx.lon is not None else 2.3522,
        "current": "european_aqi",
    }
    return f"https://air-quality-api.open-meteo.com/v1/air-quality?{urlencode(params)}"


def _qualite_aqi(aqi) -> str:
    """Libellé qualitatif de l'indice AQI européen (0-100+)."""
    if aqi is None:
        return ""
    paliers = [(20, "Bon"), (40, "Correct"), (60, "Moyen"), (80, "Mauvais"), (100, "Très mauvais")]
    for seuil, label in paliers:
        if aqi <= seuil:
            return label
    return "Extrêmement mauvais"


def parse_air(payload) -> dict:
    current = payload.get("current", {})
    aqi = current.get("european_aqi")
    return enveloppe(
        rendu="stat",
        titre="Qualité de l'air",
        data={
            "valeur": aqi,
            "unite": "AQI",
            "label": _qualite_aqi(aqi) + " (indice européen)",
        },
    )


source_air = Source(
    id="air",
    nom="Qualité de l'air",
    theme="météo",
    acces="keyless",
    besoin_geo=True,
    rendu="stat",
    ttl=30 * 60,
    attribution="Open-Meteo.com (CAMS) — CC BY 4.0",
    description="Indice de qualité de l'air européen (AQI) courant.",
    build_url=_air_url,
    parse=parse_air,
)


# ---------------------------------------------------------------------------
# 5) Hub'Eau hydrométrie — stations de mesure des cours d'eau proches
#    Rendu : carte (stations). Géolocalisé via lat/lon (distance en km).
# ---------------------------------------------------------------------------


def _hydro_url(ctx: Context) -> str:
    params = {"format": "json", "size": 20, "distance": 15}
    if ctx.lat is not None and ctx.lon is not None:
        params["latitude"] = ctx.lat
        params["longitude"] = ctx.lon
    # v2 : la v1 du référentiel renvoie 403 (bloquée).
    base = "https://hubeau.eaufrance.fr/api/v2/hydrometrie/referentiel/stations"
    return f"{base}?{urlencode(params)}"


def parse_hydro(payload) -> dict:
    data = payload.get("data", [])
    markers = []
    centre = None
    for s in data:
        lat = s.get("latitude_station")
        lon = s.get("longitude_station")
        if lat is None or lon is None:
            continue
        if centre is None:
            centre = [lat, lon]
        cours = s.get("libelle_cours_eau") or ""
        nom = s.get("libelle_station") or "Station"
        markers.append(
            {"lat": lat, "lon": lon, "popup": f"<b>{nom}</b><br>{cours}"}
        )
    return enveloppe(
        rendu="carte",
        titre="Stations hydrométriques proches",
        data={"centre": centre, "markers": markers},
    )


source_hydro = Source(
    id="hydro",
    nom="Hydrométrie (Hub'Eau)",
    theme="eau",
    acces="keyless",
    besoin_geo=True,
    rendu="carte",
    ttl=30 * 60,
    attribution="Hub'Eau / Eaufrance — Licence Ouverte",
    description="Stations de mesure des cours d'eau à proximité.",
    build_url=_hydro_url,
    parse=parse_hydro,
)


# ---------------------------------------------------------------------------
# 6) Recherche d'entreprises — recherche-entreprises.api.gouv.fr
#    Rendu : liste. Géolocalisé via code INSEE (filtre commune).
# ---------------------------------------------------------------------------


def _entreprises_url(ctx: Context) -> str:
    # Le filtre géo fiable de l'API est code_postal (code_commune ne renvoie
    # qu'un résultat). On retombe sur q si pas de code postal.
    params = {"per_page": 10, "page": 1}
    if ctx.code_postal:
        params["code_postal"] = ctx.code_postal
    elif ctx.q:
        params["q"] = ctx.q
    return f"https://recherche-entreprises.api.gouv.fr/search?{urlencode(params)}"


def parse_entreprises(payload) -> dict:
    results = payload.get("results", [])
    items = []
    for r in results:
        siege = r.get("siege") or {}
        ville = siege.get("libelle_commune") or ""
        activite = r.get("activite_principale") or ""
        items.append(
            {
                "titre": r.get("nom_complet") or r.get("nom_raison_sociale") or "?",
                "sous_titre": " · ".join(x for x in (ville, activite) if x),
            }
        )
    return enveloppe(
        rendu="liste",
        titre="Entreprises locales",
        data={"items": items},
    )


source_entreprises = Source(
    id="entreprises",
    nom="Recherche d'entreprises",
    theme="société",
    acces="keyless",
    besoin_geo=True,
    rendu="liste",
    ttl=60 * 60,
    attribution="recherche-entreprises.api.gouv.fr — Licence Ouverte",
    description="Entreprises immatriculées dans la commune.",
    build_url=_entreprises_url,
    parse=parse_entreprises,
)


# ---------------------------------------------------------------------------
# 7) Jours fériés — calendrier.api.gouv.fr (national, non géolocalisé)
#    Rendu : liste.
# ---------------------------------------------------------------------------


def _jours_feries_url(ctx: Context) -> str:
    # Endpoint par année : évite de récupérer une décennie de dates.
    annee = datetime.date.today().year
    return f"https://calendrier.api.gouv.fr/jours-feries/metropole/{annee}.json"


def parse_jours_feries(payload) -> dict:
    # payload = {"2026-01-01": "1er janvier", ...}
    items = [
        {"titre": nom, "sous_titre": date}
        for date, nom in sorted(payload.items())
    ]
    return enveloppe(
        rendu="liste",
        titre="Jours fériés (métropole)",
        data={"items": items},
    )


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


# ---------------------------------------------------------------------------
# 8) Open Food Facts — produits populaires + Nutri-Score (non géolocalisé)
#    Rendu : tableau. Widget "fun".
# ---------------------------------------------------------------------------


def _off_url(ctx: Context) -> str:
    params = {
        "fields": "product_name,brands,nutriscore_grade",
        "sort_by": "popularity_key",
        "page_size": 12,
    }
    if ctx.q:
        params["categories_tags_fr"] = ctx.q
    return f"https://fr.openfoodfacts.org/api/v2/search?{urlencode(params)}"


def parse_off(payload) -> dict:
    produits = payload.get("products", [])
    lignes = []
    for p in produits:
        nom = p.get("product_name") or "?"
        marque = p.get("brands") or ""
        nutri = (p.get("nutriscore_grade") or "?").upper()
        lignes.append([nom, marque, nutri])
    return enveloppe(
        rendu="tableau",
        titre="Open Food Facts — produits populaires",
        data={"colonnes": ["Produit", "Marque", "Nutri-Score"], "lignes": lignes},
    )


source_off = Source(
    id="openfoodfacts",
    nom="Open Food Facts",
    theme="alimentation",
    acces="keyless",
    besoin_geo=False,
    rendu="tableau",
    ttl=24 * 3600,
    attribution="Open Food Facts — ODbL",
    description="Produits alimentaires populaires et leur Nutri-Score.",
    build_url=_off_url,
    parse=parse_off,
)


# ---------------------------------------------------------------------------
# 9) DVF — prix des transactions immobilières par commune
#    Rendu : stat (prix médian au m²). Géolocalisé via code INSEE.
# ---------------------------------------------------------------------------


# Dataset DVF géolocalisé hébergé sur le portail public Opendatasoft.
_DVF_DS = "buildingref-france-demande-de-valeurs-foncieres-geolocalisee-millesime"
_DVF_BASE = (
    f"https://public.opendatasoft.com/api/explore/v2.1/catalog/datasets/{_DVF_DS}/records"
)


def _dvf_url(ctx: Context) -> str:
    # Filtre par DISTANCE autour du point (robuste aux arrondissements, où le
    # code INSEE global ne contient aucune transaction).
    lat = ctx.lat if ctx.lat is not None else 46.6
    lon = ctx.lon if ctx.lon is not None else 2.4
    where = (
        f"within_distance(geo_point, geom'POINT({lon} {lat})', 1000m) "
        'and type_local in ("Maison", "Appartement")'
    )
    params = {
        "where": where,
        "select": "valeur_fonciere,surface_reelle_bati,type_local",
        "limit": 100,
    }
    return f"{_DVF_BASE}?{urlencode(params)}"


def parse_dvf(payload) -> dict:
    """Calcule le prix médian au m² (maisons + appartements) à proximité."""
    resultats = payload.get("results", [])
    ratios = []
    for t in resultats:
        valeur = t.get("valeur_fonciere")
        surface = t.get("surface_reelle_bati")
        try:
            valeur = float(valeur)
            surface = float(surface)
        except (TypeError, ValueError):
            continue
        if surface > 0 and valeur > 0:
            ratios.append(valeur / surface)
    mediane = round(statistics.median(ratios)) if ratios else None
    return enveloppe(
        rendu="stat",
        titre="Immobilier (DVF)",
        data={
            "valeur": mediane,
            "unite": "€/m²",
            "label": f"Prix médian au m² — {len(ratios)} ventes (1 km)",
        },
    )


source_dvf = Source(
    id="dvf",
    nom="Prix immobilier (DVF)",
    theme="immobilier",
    acces="keyless",
    besoin_geo=True,
    rendu="stat",
    ttl=24 * 24 * 3600,  # ~24 jours
    attribution="DVF (Etalab/DGFiP) via public.opendatasoft.com — Licence Ouverte",
    description="Prix médian au m² des transactions de la commune.",
    build_url=_dvf_url,
    parse=parse_dvf,
)


# ---------------------------------------------------------------------------
# Liste exposée au reste du backend.
# ---------------------------------------------------------------------------

SOURCES: list[Source] = [
    source_geo_commune,
    source_meteo,
    source_carburants,
    source_air,
    source_hydro,
    source_entreprises,
    source_jours_feries,
    source_off,
    source_dvf,
]
