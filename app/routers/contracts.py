"""Contracts and coverage lookup."""

from __future__ import annotations

from typing import List

from fastapi import APIRouter, Depends

from ..deps import get_orchestrator, not_found
from ..models import Contract, Coverage
from ..orchestrator import ServiceOrchestrator
from ..store import get_store

router = APIRouter(prefix="/contracts", tags=["Contracts"])


@router.get("", response_model=List[Contract])
def list_contracts() -> List[Contract]:
    return list(get_store().contracts.values())


@router.get("/coverage", response_model=Coverage)
def check_coverage(
    generator_id: str,
    orch: ServiceOrchestrator = Depends(get_orchestrator),
) -> Coverage:
    """Return the best active contract coverage for a generator today."""
    try:
        generator = orch.store.require_generator(generator_id)
    except KeyError as exc:
        raise not_found(str(exc))
    return orch.contracts.coverage(generator.customer_id, generator.id)
