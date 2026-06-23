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
