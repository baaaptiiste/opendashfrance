"""Application Flask : API du dashboard + service du frontend statique.

Endpoints :
    GET /api/sources                 -> catalogue (métadonnées + disponibilité)
    GET /api/geocode?q=              -> géocodage BAN (ville/CP -> lat/lon/insee)
    GET /api/data/<source_id>?...    -> données normalisées d'une source

Lancement : ``python -m backend.app`` (depuis la racine du dépôt).
"""

from __future__ import annotations

from pathlib import Path

from flask import Flask, jsonify, request, send_from_directory

from . import config, geocode
from .fetcher import fetch
from .registry import Context, all_sources, get_source

# Dossier du frontend (servi en statique par Flask en dev).
FRONTEND_DIR = Path(__file__).resolve().parent.parent / "frontend"

app = Flask(__name__, static_folder=None)


# --- Frontend statique -----------------------------------------------------


@app.route("/")
def index():
    return send_from_directory(FRONTEND_DIR, "index.html")


@app.route("/<path:filename>")
def static_files(filename: str):
    return send_from_directory(FRONTEND_DIR, filename)


# --- API -------------------------------------------------------------------


@app.route("/api/sources")
def api_sources():
    """Catalogue des sources. Une source 'key' sans clé -> disponible=False."""
    catalogue = [
        s.to_catalog_dict(disponible=config.has_api_key(s.env_var) or s.acces == "keyless")
        for s in all_sources()
    ]
    return jsonify(catalogue)


@app.route("/api/geocode")
def api_geocode():
    q = request.args.get("q", "")
    result = geocode.geocode(q)
    if result is None:
        return jsonify({"erreur": "Adresse introuvable"}), 404
    return jsonify(result)


@app.route("/api/data/<source_id>")
def api_data(source_id: str):
    source = get_source(source_id)
    if source is None:
        return jsonify({"erreur": "Source inconnue"}), 404

    # Source 'key' sans clé : indisponible explicite (pas d'appel réseau).
    if source.acces == "key" and not config.has_api_key(source.env_var):
        return jsonify(
            {
                "rendu": source.rendu,
                "titre": source.nom,
                "erreur": "Clé API requise (source désactivée)",
                "disponible": False,
            }
        )

    ctx = Context.from_request_args(request.args)
    if source.besoin_geo and ctx.lat is None and ctx.code_insee is None:
        return jsonify(
            {
                "rendu": source.rendu,
                "titre": source.nom,
                "erreur": "Sélectionnez d'abord une localisation",
                "disponible": False,
            }
        )

    return jsonify(fetch(source, ctx))


def main() -> None:
    app.run(host=config.HOST, port=config.PORT, debug=True)


if __name__ == "__main__":
    main()
