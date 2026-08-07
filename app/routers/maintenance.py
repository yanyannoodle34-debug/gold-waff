"""Maintenance scheduler: list due generators and run the daily scheduler."""

from __future__ import annotations

from typing import List

from fastapi import APIRouter, Depends

from ..deps import get_orchestrator
from ..models import Generator
from ..orchestrator import ServiceOrchestrator
from ..schemas import DispatchResponse

router = APIRouter(prefix="/maintenance", tags=["Maintenance"])


@router.get("/due", response_model=List[Generator])
def list_due(
    orch: ServiceOrchestrator = Depends(get_orchestrator),
) -> List[Generator]:
    """Generators currently due for preventive maintenance."""
    return orch.maintenance.generators_due()


@router.post("/run-daily", response_model=List[DispatchResponse])
def run_daily(
    orch: ServiceOrchestrator = Depends(get_orchestrator),
) -> List[DispatchResponse]:
    """Run the daily scheduler: create + dispatch PM work orders for due units."""
    results = orch.schedule_preventive_maintenance()
    return [DispatchResponse.from_result(r) for r in results]
