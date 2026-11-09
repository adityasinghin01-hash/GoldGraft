"""FastAPI application for GoldGraft backend (pieces.backend).

Fulfills GU01/GU02 API contracts, serving all routes defined in
goldgraft_contracts.api_routes.
"""

from .app import app, create_app

__all__ = ["app", "create_app"]
