"""Factories pour fabriquer des sources sans dupliquer le boilerplate.

La plus importante : ``opendatasoft_source``. Énormément de portails publics
français (data.economie.gouv.fr, ADEME, data.education.gouv.fr, open data des
villes...) tournent sur le moteur Opendatasoft (ODS). Leur API v2.1 partage le
même endpoint :

    https://<domain>/api/explore/v2.1/catalog/datasets/<dataset_id>/records

On encapsule ce pattern : ajouter une nouvelle source ODS = un seul appel à
``opendatasoft_source(...)`` en fournissant le domaine, le dataset_id et un
parser.
"""

from __future__ import annotations

from collections.abc import Callable
from urllib.parse import urlencode

from .base import Context, Source


def opendatasoft_source(
    *,
    id: str,
    nom: str,
    theme: str,
    domain: str,
    dataset_id: str,
    rendu: str,
    parse: Callable[[dict], dict],
    ttl: int,
    attribution: str,
    description: str = "",
    geo_field: str | None = None,
    rayon_m: int = 5000,
    limit: int = 20,
    extra_params: dict | None = None,
) -> Source:
    """Fabrique une source basée sur l'API Explore v2.1 d'Opendatasoft.

    Args:
        domain      hôte du portail ODS (ex. "data.economie.gouv.fr").
        dataset_id  identifiant du dataset ODS.
        geo_field   nom du champ géo du dataset ; si fourni, on filtre par
                    distance autour de (lat, lon) du contexte.
        rayon_m     rayon de recherche en mètres (si geo_field).
        limit       nombre max d'enregistrements.
        extra_params query params ODS supplémentaires (where, select, order_by...).
    """
    besoin_geo = geo_field is not None
    base = f"https://{domain}/api/explore/v2.1/catalog/datasets/{dataset_id}/records"

    def build_url(ctx: Context) -> str:
        params: dict[str, str | int] = {"limit": limit}
        if extra_params:
            params.update(extra_params)
        if geo_field and ctx.lat is not None and ctx.lon is not None:
            # Syntaxe ODS : within_distance(champ, geom'POINT(lon lat)', dist)
            point = f"geom'POINT({ctx.lon} {ctx.lat})'"
            params["where"] = (
                f"within_distance({geo_field}, {point}, {rayon_m}m)"
            )
        return f"{base}?{urlencode(params)}"

    return Source(
        id=id,
        nom=nom,
        theme=theme,
        acces="keyless",
        besoin_geo=besoin_geo,
        rendu=rendu,
        ttl=ttl,
        attribution=attribution,
        description=description,
        build_url=build_url,
        parse=parse,
        env_var=None,
    )
