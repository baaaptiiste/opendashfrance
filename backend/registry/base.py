"""Schéma du registre de sources.

Cœur du projet : chaque source de données publique est décrite par un objet
``Source`` (configuration + 2 fonctions). L'UI ne contient AUCUN code spécifique
à une source : elle se contente de lire le type de rendu et d'appeler le
renderer générique correspondant.

Ajouter une source = ajouter un ``Source`` au catalogue (voir sources.py).
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

# Types de rendu reconnus par le frontend (1 renderer JS par valeur).
RENDUS = {"carte", "graphe", "liste", "stat", "tableau"}

# Thèmes proposés dans la galerie (extensible librement).
THEMES = {
    "énergie",
    "eau",
    "météo",
    "société",
    "immobilier",
    "culture",
    "alimentation",
}


@dataclass(frozen=True)
class Context:
    """Contexte transmis aux sources géolocalisées.

    Rempli à partir des query params de /api/data/<id>. Tout est optionnel :
    une source non géolocalisée ignore simplement ces champs.
    """

    lat: float | None = None
    lon: float | None = None
    code_insee: str | None = None
    q: str | None = None

    @classmethod
    def from_request_args(cls, args: dict) -> Context:
        """Construit un Context depuis les query params (valeurs str -> float)."""

        def _float(key: str) -> float | None:
            val = args.get(key)
            try:
                return float(val) if val not in (None, "") else None
            except (TypeError, ValueError):
                return None

        return cls(
            lat=_float("lat"),
            lon=_float("lon"),
            code_insee=(args.get("code_insee") or None),
            q=(args.get("q") or None),
        )


@dataclass(frozen=True)
class Source:
    """Description complète d'une source de données.

    Attributs :
        id          identifiant stable (slug), utilisé dans les URLs.
        nom         libellé affiché.
        theme       clé de regroupement dans la galerie (voir THEMES).
        acces       "keyless" (libre) ou "key" (nécessite une clé API).
        env_var     nom de la variable d'env portant la clé (si acces="key").
        besoin_geo  True si la source a besoin de lat/lon/code_insee.
        rendu       type de rendu (voir RENDUS).
        ttl         durée de cache en secondes.
        attribution crédit + licence (affiché dans le widget et le README).
        build_url   (Context) -> URL d'appel HTTP.
        parse       (réponse JSON) -> enveloppe normalisée (voir parse() plus bas).
    """

    id: str
    nom: str
    theme: str
    acces: str
    besoin_geo: bool
    rendu: str
    ttl: int
    attribution: str
    build_url: Callable[[Context], str]
    parse: Callable[[dict], dict]
    env_var: str | None = None
    description: str = ""

    def __post_init__(self) -> None:
        # Validations légères pour attraper les fautes de frappe au chargement.
        if self.rendu not in RENDUS:
            raise ValueError(f"Source {self.id}: rendu inconnu {self.rendu!r}")
        if self.acces not in {"keyless", "key"}:
            raise ValueError(f"Source {self.id}: acces invalide {self.acces!r}")
        if self.acces == "key" and not self.env_var:
            raise ValueError(f"Source {self.id}: acces 'key' exige env_var")

    def to_catalog_dict(self, *, disponible: bool) -> dict:
        """Sérialise les MÉTADONNÉES pour /api/sources (sans les callables)."""
        return {
            "id": self.id,
            "nom": self.nom,
            "theme": self.theme,
            "acces": self.acces,
            "besoin_geo": self.besoin_geo,
            "rendu": self.rendu,
            "ttl": self.ttl,
            "attribution": self.attribution,
            "description": self.description,
            "env_var": self.env_var,
            # False si source "key" sans clé -> le front la grise.
            "disponible": disponible,
        }


def enveloppe(rendu: str, titre: str, data: dict, **extra) -> dict:
    """Construit l'enveloppe normalisée renvoyée par tous les parsers.

    Contrat partagé avec le frontend :
        {"rendu": ..., "titre": ..., "data": {...}}

    La forme de ``data`` dépend du rendu (voir README / renderers JS).
    """
    payload = {"rendu": rendu, "titre": titre, "data": data}
    payload.update(extra)
    return payload
