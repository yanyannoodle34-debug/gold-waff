"""Response schemas that wrap orchestrator results for the API."""

from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel

from .models import (
    Coverage,
    PartReservation,
    PurchaseRequest,
    Technician,
    WorkOrder,
)
from .orchestrator import DispatchResult


class DispatchResponse(BaseModel):
    """Serialized outcome of creating and dispatching a work order."""

    work_order: WorkOrder
    technician: Optional[Technician] = None
    coverage: Coverage
    reservations: List[PartReservation] = []
    purchase_requests: List[PurchaseRequest] = []

    @classmethod
    def from_result(cls, result: DispatchResult) -> "DispatchResponse":
        return cls(
            work_order=result.work_order,
            technician=result.technician,
            coverage=result.coverage,
            reservations=result.reservation.reservations,
            purchase_requests=result.reservation.purchase_requests,
        )
