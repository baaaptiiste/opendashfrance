"""Tests des parsers et constructeurs d'URL — 100 % hors-ligne (fixtures mockées).

On vérifie le contrat de l'enveloppe normalisée et la robustesse des parsers.
"""

from __future__ import annotations

from backend.geocode import parse_ban
from backend.registry import REGISTRY, Context
from backend.registry.sources import (
    parse_air,
    parse_carburants,
    parse_dvf,
    parse_entreprises,
    parse_geo_commune,
    parse_hydro,
    parse_jours_feries,
    parse_meteo,
    parse_off,
)

# --- Enveloppe / contrat commun -------------------------------------------


def _assert_enveloppe(env, rendu):
    assert env["rendu"] == rendu
    assert "titre" in env
    assert "data" in env


# --- Géo commune (stat) ----------------------------------------------------


def test_parse_geo_commune(fx_geo_commune):
    env = parse_geo_commune(fx_geo_commune)
    _assert_enveloppe(env, "stat")
    assert env["data"]["valeur"] == 522969
    assert env["data"]["unite"] == "habitants"
    assert "69123" in env["data"]["label"]
    assert "Lyon" in env["titre"]


def test_parse_geo_commune_vide():
    import pytest

    with pytest.raises(ValueError):
        parse_geo_commune([])


# --- Météo (graphe) --------------------------------------------------------


def test_parse_meteo(fx_meteo):
    env = parse_meteo(fx_meteo)
    _assert_enveloppe(env, "graphe")
    d = env["data"]
    assert d["type"] == "line"
    assert d["labels"] == ["00:00", "01:00", "02:00", "03:00"]
    assert d["series"][0]["points"] == [18.2, 17.5, 17.1, 16.8]
    assert "°C" in d["series"][0]["nom"]


# --- Carburants (carte) ----------------------------------------------------


def test_parse_carburants(fx_carburants):
    env = parse_carburants(fx_carburants)
    _assert_enveloppe(env, "carte")
    markers = env["data"]["markers"]
    # 3 résultats mais 1 sans coordonnées -> ignoré.
    assert len(markers) == 2
    assert env["data"]["centre"] == [45.7589, 4.8351]
    # Le popup agrège les prix présents.
    assert "GAZOLE" in markers[0]["popup"]
    assert "SP95" in markers[0]["popup"]
    assert "E85" in markers[1]["popup"]


def test_parse_carburants_vide():
    env = parse_carburants({"results": []})
    assert env["data"]["markers"] == []
    assert env["data"]["centre"] is None


# --- BAN (géocodage) -------------------------------------------------------


def test_parse_ban(fx_ban):
    loc = parse_ban(fx_ban)
    assert loc["lat"] == 45.7589
    assert loc["lon"] == 4.8351
    assert loc["code_insee"] == "69123"
    assert loc["ville"] == "Lyon"


def test_parse_ban_vide():
    assert parse_ban({"features": []}) is None


# --- Qualité de l'air (stat) ----------------------------------------------


def test_parse_air(fx_air):
    env = parse_air(fx_air)
    _assert_enveloppe(env, "stat")
    assert env["data"]["valeur"] == 34
    assert env["data"]["unite"] == "AQI"
    assert "Correct" in env["data"]["label"]  # 34 -> palier <=40


# --- Hydrométrie (carte) ---------------------------------------------------


def test_parse_hydro(fx_hydro):
    env = parse_hydro(fx_hydro)
    _assert_enveloppe(env, "carte")
    markers = env["data"]["markers"]
    assert len(markers) == 2  # 3e station sans coords ignorée
    assert env["data"]["centre"] == [45.7589, 4.8351]
    assert "Rhône" in markers[0]["popup"]


# --- Entreprises (liste) ---------------------------------------------------


def test_parse_entreprises(fx_entreprises):
    env = parse_entreprises(fx_entreprises)
    _assert_enveloppe(env, "liste")
    items = env["data"]["items"]
    assert len(items) == 2
    assert items[0]["titre"] == "BOULANGERIE DUPONT"
    assert "LYON" in items[0]["sous_titre"]


# --- Jours fériés (liste) --------------------------------------------------


def test_parse_jours_feries(fx_jours_feries):
    env = parse_jours_feries(fx_jours_feries)
    _assert_enveloppe(env, "liste")
    items = env["data"]["items"]
    assert len(items) == 4
    # Triés par date.
    assert items[0]["sous_titre"] == "2026-01-01"
    assert items[-1]["sous_titre"] == "2026-12-25"


# --- Open Food Facts (tableau) ---------------------------------------------


def test_parse_off(fx_off):
    env = parse_off(fx_off)
    _assert_enveloppe(env, "tableau")
    assert env["data"]["colonnes"] == ["Produit", "Marque", "Nutri-Score"]
    lignes = env["data"]["lignes"]
    assert lignes[0] == ["Nutella", "Ferrero", "E"]
    assert len(lignes) == 3


# --- DVF immobilier (stat) -------------------------------------------------


def test_parse_dvf(fx_dvf):
    env = parse_dvf(fx_dvf)
    _assert_enveloppe(env, "stat")
    # ratios = [4000, 4500, 5000] -> médiane 4500 ; surface 0 exclue
    assert env["data"]["valeur"] == 4500
    assert env["data"]["unite"] == "€/m²"
    assert "3 ventes" in env["data"]["label"]


def test_parse_dvf_vide():
    env = parse_dvf({"results": []})
    assert env["data"]["valeur"] is None


# --- build_url -------------------------------------------------------------


def test_build_url_carburants_distance():
    from urllib.parse import unquote_plus

    src = REGISTRY["carburants"]
    url = unquote_plus(src.build_url(Context(lat=45.75, lon=4.83)))
    assert "within_distance" in url
    assert "datasets/prix-des-carburants-en-france-flux-instantane-v2/records" in url
    # ODS attend POINT(lon lat)
    assert "POINT(4.83 45.75)" in url


def test_build_url_geo_commune_par_insee():
    src = REGISTRY["geo-commune"]
    url = src.build_url(Context(code_insee="69123"))
    assert "code=69123" in url
    assert "geo.api.gouv.fr/communes" in url


def test_build_url_meteo_defaut_paris():
    src = REGISTRY["meteo"]
    url = src.build_url(Context())  # sans géo -> repli Paris
    assert "latitude=48.8566" in url
    assert "hourly=temperature_2m" in url
