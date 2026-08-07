"""Dispatch preview: rank technicians for a hypothetical job."""

from __future__ import annotations

from typing import List

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from ..deps import get_orchestrator, not_found
from ..models import Priority, WorkOrder, WorkOrderType
from ..orchestrator import ServiceOrchestrator

router = APIRouter(prefix="/dispatch", tags=["Dispatch"])


class DispatchPreviewIn(BaseModel):
    generator_id: str
    type: WorkOrderType = WorkOrderType.BREAKDOWN
    priority: Priority = Priority.EMERGENCY


class CandidateOut(BaseModel):
    technician_id: str
    technician_name: str
    score: float
    distance_km: float


@router.post("/preview", response_model=List[CandidateOut])
def preview_dispatch(
    body: DispatchPreviewIn,
    orch: ServiceOrchestrator = Depends(get_orchestrator),
) -> List[CandidateOut]:
    """Return ranked technician candidates without creating a work order."""
    try:
        generator = orch.store.require_generator(body.generator_id)
    except KeyError as exc:
        raise not_found(str(exc))

    probe = WorkOrder(
        id="PREVIEW",
        generator_id=generator.id,
        customer_id=generator.customer_id,
        type=body.type,
        priority=body.priority,
    )
    ranked = orch.dispatch.rank_candidates(probe, generator)
    return [
        CandidateOut(
            technician_id=c.technician.id,
            technician_name=c.technician.name,
            score=round(c.score, 4),
            distance_km=c.distance_km,
        )
        for c in ranked
    ]
