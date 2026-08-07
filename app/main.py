"""FastAPI application for the Generator Service Orchestration Framework.

Wires the routers together and seeds the in-memory store on startup so the API
is immediately usable with representative data.
"""

from __future__ import annotations

from fastapi import FastAPI

from . import __version__
from .routers import (
    contracts,
    customers,
    dispatch,
    generators,
    incidents,
    inventory,
    maintenance,
    reporting,
    technicians,
    work_orders,
)
from .seed import seed_store
from .store import InMemoryStore, set_store

DESCRIPTION = """
Coordinates the full service lifecycle for an electrical & diesel generator
service company: customer & asset registration, preventive-maintenance
scheduling, emergency-breakdown dispatch, spare-parts inventory, field
technician actions, contract coverage, billing, predictive maintenance, and
reporting.
"""


def create_app(seed: bool = True) -> FastAPI:
    """Build the FastAPI app, optionally seeding a fresh store."""
    store = InMemoryStore()
    if seed:
        seed_store(store)
    set_store(store)

    app = FastAPI(
        title="Generator Service Orchestration Framework",
        description=DESCRIPTION,
        version=__version__,
    )

    for module in (
        customers,
        generators,
        technicians,
        contracts,
        incidents,
        work_orders,
        dispatch,
        inventory,
        maintenance,
        reporting,
    ):
        app.include_router(module.router)

    @app.get("/", tags=["Meta"])
    def root() -> dict:
        return {
            "service": "Generator Service Orchestration Framework",
            "version": __version__,
            "docs": "/docs",
        }

    @app.get("/health", tags=["Meta"])
    def health() -> dict:
        return {"status": "ok"}

    return app


app = create_app()
