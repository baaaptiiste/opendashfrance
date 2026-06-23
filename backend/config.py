"""Configuration centrale : lecture du .env et exposition des réglages.

Toutes les clés API sont OPTIONNELLES. Le dashboard fonctionne sans .env.
On expose un helper ``get_api_key(env_var)`` qui renvoie la clé si elle existe,
sinon ``None`` — ce qui permet au registre de griser les sources "key".
"""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

# Charge le .env s'il existe (silencieux sinon).
load_dotenv()

# Racine du package backend (pour résoudre les chemins relatifs).
BACKEND_DIR = Path(__file__).resolve().parent

# --- Serveur ---
HOST: str = os.getenv("OPENDASH_HOST", "127.0.0.1")
# PORT (standard) prioritaire — permet aux outils d'attribuer un port libre.
PORT: int = int(os.getenv("PORT") or os.getenv("OPENDASH_PORT") or "5000")

# --- Cache SQLite ---
CACHE_PATH: Path = Path(
    os.getenv("OPENDASH_CACHE_PATH", str(BACKEND_DIR / "cache.sqlite"))
)


def get_api_key(env_var: str | None) -> str | None:
    """Renvoie la valeur de la variable d'env demandée, ou None si absente/vide."""
    if not env_var:
        return None
    value = os.getenv(env_var)
    return value or None


def has_api_key(env_var: str | None) -> bool:
    """True si la clé est disponible (source 'key' activable)."""
    return get_api_key(env_var) is not None
