"""Point d'accès au registre de sources.

Expose ``REGISTRY`` (dict id -> Source) et quelques helpers. Importer depuis
ici, jamais directement depuis sources.py, pour garder un seul point d'entrée.
"""

from __future__ import annotations

from .base import Context, Source, enveloppe
from .sources import SOURCES

# Index par id pour un accès O(1) depuis les routes.
REGISTRY: dict[str, Source] = {s.id: s for s in SOURCES}


def get_source(source_id: str) -> Source | None:
    """Renvoie la source par id, ou None si inconnue."""
    return REGISTRY.get(source_id)


def all_sources() -> list[Source]:
    """Liste de toutes les sources déclarées."""
    return list(SOURCES)


__all__ = [
    "REGISTRY",
    "Context",
    "Source",
    "enveloppe",
    "get_source",
    "all_sources",
]
