"""Fixtures partagées : chargement des réponses API mockées (zéro réseau)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

FIXTURES = Path(__file__).parent / "fixtures"


def _load(name: str):
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))


@pytest.fixture
def fx_geo_commune():
    return _load("geo_commune.json")


@pytest.fixture
def fx_meteo():
    return _load("meteo.json")


@pytest.fixture
def fx_carburants():
    return _load("carburants.json")


@pytest.fixture
def fx_ban():
    return _load("ban.json")


@pytest.fixture
def fx_air():
    return _load("air.json")


@pytest.fixture
def fx_hydro():
    return _load("hydro.json")


@pytest.fixture
def fx_entreprises():
    return _load("entreprises.json")


@pytest.fixture
def fx_jours_feries():
    return _load("jours_feries.json")


@pytest.fixture
def fx_off():
    return _load("openfoodfacts.json")


@pytest.fixture
def fx_dvf():
    return _load("dvf.json")
