"""Tests du cache SQLite : set/get, expiration TTL."""

from __future__ import annotations

import time

from backend import cache


def test_set_get(tmp_path):
    db = tmp_path / "c.sqlite"
    cache.set("k", {"a": 1}, ttl=60, db_path=db)
    assert cache.get("k", db_path=db) == {"a": 1}


def test_get_absent(tmp_path):
    db = tmp_path / "c.sqlite"
    assert cache.get("inconnu", db_path=db) is None


def test_expiration(tmp_path):
    db = tmp_path / "c.sqlite"
    cache.set("k", {"v": 1}, ttl=-1, db_path=db)  # déjà expiré
    assert cache.get("k", db_path=db) is None


def test_clear(tmp_path):
    db = tmp_path / "c.sqlite"
    cache.set("k", {"v": 1}, ttl=60, db_path=db)
    cache.clear(db_path=db)
    assert cache.get("k", db_path=db) is None


def test_ttl_actif(tmp_path):
    db = tmp_path / "c.sqlite"
    cache.set("k", {"v": 1}, ttl=1, db_path=db)
    assert cache.get("k", db_path=db) == {"v": 1}
    time.sleep(1.1)
    assert cache.get("k", db_path=db) is None
