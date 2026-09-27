"""Shared test fixtures.

Each test gets a fresh seeded store and an orchestrator over it, plus a
TestClient whose app is bound to that same store, so API and unit tests observe
identical state.
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.main import create_app
from app.orchestrator import ServiceOrchestrator
from app.seed import seed_store
from app.store import InMemoryStore, set_store


@pytest.fixture
def store() -> InMemoryStore:
    fresh = InMemoryStore()
    seed_store(fresh)
    set_store(fresh)
    return fresh


@pytest.fixture
def orch(store: InMemoryStore) -> ServiceOrchestrator:
    return ServiceOrchestrator(store)


@pytest.fixture
def client() -> TestClient:
    # create_app builds and installs a fresh seeded store via set_store.
    app = create_app(seed=True)
    return TestClient(app)
