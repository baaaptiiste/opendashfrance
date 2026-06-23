"""Cache SQLite simple avec TTL par entrée.

Une seule table ``cache(cle, valeur_json, expire_at)``. On stocke le JSON
normalisé déjà parsé : un hit cache évite à la fois l'appel réseau ET le parsing.

Thread-safe pour le serveur de dev Flask : on ouvre une connexion par appel
(SQLite gère le verrouillage fichier) — suffisant pour la volumétrie visée.
"""

from __future__ import annotations

import json
import sqlite3
import time
from pathlib import Path

from . import config

_SCHEMA = """
CREATE TABLE IF NOT EXISTS cache (
    cle        TEXT PRIMARY KEY,
    valeur     TEXT NOT NULL,
    expire_at  REAL NOT NULL
);
"""


def _connect(db_path: Path | None = None) -> sqlite3.Connection:
    path = db_path or config.CACHE_PATH
    conn = sqlite3.connect(path)
    conn.execute(_SCHEMA)
    return conn


def get(cle: str, db_path: Path | None = None) -> dict | None:
    """Renvoie la valeur en cache si présente ET non expirée, sinon None."""
    conn = _connect(db_path)
    try:
        row = conn.execute(
            "SELECT valeur, expire_at FROM cache WHERE cle = ?", (cle,)
        ).fetchone()
        if row is None:
            return None
        valeur, expire_at = row
        if expire_at < time.time():
            # Entrée périmée : on la purge au passage.
            conn.execute("DELETE FROM cache WHERE cle = ?", (cle,))
            conn.commit()
            return None
        return json.loads(valeur)
    finally:
        conn.close()


def set(cle: str, valeur: dict, ttl: int, db_path: Path | None = None) -> None:
    """Stocke ``valeur`` sous ``cle`` avec une durée de vie de ``ttl`` secondes."""
    expire_at = time.time() + ttl
    conn = _connect(db_path)
    try:
        conn.execute(
            "INSERT OR REPLACE INTO cache (cle, valeur, expire_at) VALUES (?, ?, ?)",
            (cle, json.dumps(valeur, ensure_ascii=False), expire_at),
        )
        conn.commit()
    finally:
        conn.close()


def clear(db_path: Path | None = None) -> None:
    """Vide tout le cache (utilitaire / tests)."""
    conn = _connect(db_path)
    try:
        conn.execute("DELETE FROM cache")
        conn.commit()
    finally:
        conn.close()
