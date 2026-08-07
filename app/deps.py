"""Shared FastAPI dependencies and request schemas.

Routers depend on :func:`get_orchestrator` to obtain a ServiceOrchestrator bound
to the process-wide store, and reuse the small request bodies defined here.
"""

from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from fastapi import HTTPException
from pydantic import BaseModel

from .models import PartCategory, Priority, WorkOrderType
from .orchestrator import ServiceOrchestrator
from .store import get_store


def get_orchestrator() -> ServiceOrchestrator:
    """FastAPI dependency: an orchestrator over the current store."""
    return ServiceOrchestrator(get_store())


def not_found(detail: str) -> HTTPException:
    return HTTPException(status_code=404, detail=detail)


# -- request bodies --------------------------------------------------------


class RequiredPartIn(BaseModel):
    category: PartCategory
    quantity: int = 1


class BreakdownRequest(BaseModel):
    generator_id: str
    description: str
    priority: Priority = Priority.EMERGENCY
    required_parts: List[RequiredPartIn] = []


class ServiceRequestIn(BaseModel):
    generator_id: str
    type: WorkOrderType
    priority: Priority = Priority.NORMAL
    required_parts: List[RequiredPartIn] = []
    scheduled_date: Optional[datetime] = None


class RunningHoursIn(BaseModel):
    hours: float


class FaultIn(BaseModel):
    code: str
    description: str


class ReplacePartIn(BaseModel):
    reservation_id: str


class SignatureIn(BaseModel):
    signature: str


class CloseWorkOrderIn(BaseModel):
    labor_hours: float = 0.0
    summary: str = ""
