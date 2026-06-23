"""Tests de l'orchestration fetch() : succès, cache, gestion d'erreur.

HTTP mocké avec ``responses`` — aucun appel réseau réel.
"""

from __future__ import annotations

import responses

from backend import cache, fetcher
from backend.registry import REGISTRY, Context


@responses.activate
def test_fetch_succes_et_cache(tmp_path, monkeypatch, fx_meteo):
    # Cache isolé dans un fichier temporaire.
    db = tmp_path / "cache.sqlite"
    monkeypatch.setattr(cache.config, "CACHE_PATH", db)

    src = REGISTRY["meteo"]
    ctx = Context(lat=45.75, lon=4.83)

    responses.add(responses.GET, src.build_url(ctx), json=fx_meteo, status=200)

    env = fetcher.fetch(src, ctx)
    assert env["disponible"] is True
    assert env["rendu"] == "graphe"
    assert env["_cache"] is False

    # 2e appel : doit venir du cache (aucune requête HTTP supplémentaire).
    env2 = fetcher.fetch(src, ctx)
    assert env2["_cache"] is True
    assert len(responses.calls) == 1


@responses.activate
def test_fetch_erreur_http_donne_indisponible(tmp_path, monkeypatch):
    db = tmp_path / "cache.sqlite"
    monkeypatch.setattr(cache.config, "CACHE_PATH", db)

    src = REGISTRY["meteo"]
    ctx = Context(lat=1, lon=2)
    responses.add(responses.GET, src.build_url(ctx), status=500)

    env = fetcher.fetch(src, ctx)
    assert env["disponible"] is False
    assert "erreur" in env


@responses.activate
def test_fetch_json_invalide_donne_indisponible(tmp_path, monkeypatch):
    db = tmp_path / "cache.sqlite"
    monkeypatch.setattr(cache.config, "CACHE_PATH", db)

    src = REGISTRY["geo-commune"]
    ctx = Context(code_insee="00000")
    # Réponse vide -> parser lève ValueError -> enveloppe indisponible.
    responses.add(responses.GET, src.build_url(ctx), json=[], status=200)

    env = fetcher.fetch(src, ctx)
    assert env["disponible"] is False
