"""Géocodage via la Base Adresse Nationale (BAN).

Socle du dashboard (PAS un widget) : transforme "ville ou code postal" en
{lat, lon, code_insee, label} qui alimente ensuite tous les widgets géolocalisés.

API : https://api-adresse.data.gouv.fr/search/?q=... (keyless).
"""

from __future__ import annotations

from urllib.parse import urlencode

import requests

_BAN_URL = "https://api-adresse.data.gouv.fr/search/"
_TIMEOUT = 8


def geocode(q: str, limit: int = 1) -> dict | None:
    """Géocode une requête texte. Renvoie le meilleur résultat ou None.

    Sortie : {lat, lon, code_insee, label, ville, code_postal}.
    Ne lève pas en cas d'erreur réseau : renvoie None.
    """
    if not q or not q.strip():
        return None

    params = {"q": q.strip(), "limit": limit}
    url = f"{_BAN_URL}?{urlencode(params)}"

    try:
        resp = requests.get(
            url, timeout=_TIMEOUT, headers={"User-Agent": "OpenDashFrance"}
        )
        resp.raise_for_status()
        payload = resp.json()
    except requests.RequestException:
        return None

    return parse_ban(payload)


def parse_ban(payload: dict) -> dict | None:
    """Parser pur (testable) : extrait le 1er feature GeoJSON de la BAN."""
    features = payload.get("features", [])
    if not features:
        return None
    feat = features[0]
    props = feat.get("properties", {})
    coords = feat.get("geometry", {}).get("coordinates", [None, None])
    lon, lat = coords[0], coords[1]
    return {
        "lat": lat,
        "lon": lon,
        "code_insee": props.get("citycode"),
        "code_postal": props.get("postcode"),
        "ville": props.get("city"),
        "label": props.get("label"),
    }
