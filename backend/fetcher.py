"""Orchestration : cache -> appel HTTP -> parsing -> enveloppe normalisée.

Centralise la gestion d'erreurs : si une source tombe (réseau, HTTP, parsing),
on renvoie une enveloppe d'état "indisponible" plutôt que de lever — le widget
front affiche l'erreur sans casser le reste du dashboard.
"""

from __future__ import annotations

import hashlib

import requests

from . import cache
from .registry import Context, Source

# Timeout réseau (s). Court : un widget lent ne doit pas bloquer la page.
_TIMEOUT = 8


def _cache_key(source: Source, ctx: Context) -> str:
    """Clé de cache = id source + contexte normalisé (hash court)."""
    raw = f"{source.id}|{ctx.lat}|{ctx.lon}|{ctx.code_insee}|{ctx.q}"
    digest = hashlib.sha1(raw.encode()).hexdigest()[:16]
    return f"{source.id}:{digest}"


def _indisponible(source: Source, message: str) -> dict:
    """Enveloppe d'erreur uniforme consommée par le front."""
    return {
        "rendu": source.rendu,
        "titre": source.nom,
        "erreur": message,
        "disponible": False,
    }


def fetch(source: Source, ctx: Context, *, use_cache: bool = True) -> dict:
    """Renvoie l'enveloppe normalisée pour une source dans un contexte donné.

    Ne lève jamais : toute exception devient une enveloppe "indisponible".
    """
    key = _cache_key(source, ctx)

    if use_cache:
        cached = cache.get(key)
        if cached is not None:
            cached["_cache"] = True
            return cached

    try:
        url = source.build_url(ctx)
        resp = requests.get(url, timeout=_TIMEOUT, headers={"User-Agent": "OpenDashFrance"})
        resp.raise_for_status()
        payload = resp.json()
        enveloppe = source.parse(payload)
    except requests.RequestException as exc:
        return _indisponible(source, f"Source injoignable : {exc}")
    except (ValueError, KeyError, TypeError) as exc:
        return _indisponible(source, f"Réponse illisible : {exc}")

    enveloppe["disponible"] = True
    if use_cache:
        cache.set(key, enveloppe, source.ttl)
    enveloppe["_cache"] = False
    return enveloppe
