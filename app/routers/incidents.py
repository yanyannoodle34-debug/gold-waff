"""Emergency breakdown workflow.

Reporting a breakdown creates an incident, classifies its priority, checks
contract coverage, creates a breakdown work order, dispatches the best available
technician, and reserves the parts needed -- all in one call.
"""

from __future__ import annotations

from typing import List

from fastapi import APIRouter, Depends

from ..deps import BreakdownRequest, get_orchestrator
from ..models import Incident, RequiredPart
from ..orchestrator import ServiceOrchestrator
from ..schemas import DispatchResponse
from ..store import get_store

router = APIRouter(prefix="/incidents", tags=["Emergency Breakdown"])


@router.get("", response_model=List[Incident])
def list_incidents() -> List[Incident]:
    return list(get_store().incidents.values())


@router.post("", response_model=DispatchResponse, status_code=201)
def report_breakdown(
    body: BreakdownRequest,
    orch: ServiceOrchestrator = Depends(get_orchestrator),
) -> DispatchResponse:
    required = [
        RequiredPart(category=p.category, quantity=p.quantity)
        for p in body.required_parts
    ]
    result = orch.report_breakdown(
        generator_id=body.generator_id,
        description=body.description,
        priority=body.priority,
        required_parts=required,
    )
    return DispatchResponse.from_result(result)
