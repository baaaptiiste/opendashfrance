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
# Liste exposée au reste du backend.
# ---------------------------------------------------------------------------

SOURCES: list[Source] = [
    source_geo_commune,
    source_meteo,
    source_carburants,
]
