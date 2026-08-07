"""Work orders: service requests, field-technician transitions, and close."""

from __future__ import annotations

from typing import List

from fastapi import APIRouter, Depends

from ..deps import (
    CloseWorkOrderIn,
    FaultIn,
    ReplacePartIn,
    RunningHoursIn,
    ServiceRequestIn,
    SignatureIn,
    get_orchestrator,
    not_found,
)
from ..models import Invoice, RequiredPart, WorkOrder
from ..orchestrator import ServiceOrchestrator
from ..schemas import DispatchResponse
from ..store import get_store

router = APIRouter(prefix="/work-orders", tags=["Work Orders"])


@router.get("", response_model=List[WorkOrder])
def list_work_orders() -> List[WorkOrder]:
    return list(get_store().work_orders.values())


@router.post("", response_model=DispatchResponse, status_code=201)
def create_service_request(
    body: ServiceRequestIn,
    orch: ServiceOrchestrator = Depends(get_orchestrator),
) -> DispatchResponse:
    """Create a (non-emergency) service request work order."""
    required = [
        RequiredPart(category=p.category, quantity=p.quantity)
        for p in body.required_parts
    ]
    try:
        result = orch.create_service_request(
            generator_id=body.generator_id,
            work_order_type=body.type,
            priority=body.priority,
            required_parts=required,
            scheduled_date=body.scheduled_date,
        )
    except KeyError as exc:
        raise not_found(str(exc))
    return DispatchResponse.from_result(result)


@router.get("/{work_order_id}", response_model=WorkOrder)
def get_work_order(work_order_id: str) -> WorkOrder:
    wo = get_store().work_orders.get(work_order_id)
    if wo is None:
        raise not_found(f"Unknown work order: {work_order_id}")
    return wo


# -- field-technician transitions -----------------------------------------


@router.post("/{work_order_id}/running-hours", response_model=WorkOrder)
def record_running_hours(
    work_order_id: str,
    body: RunningHoursIn,
    orch: ServiceOrchestrator = Depends(get_orchestrator),
) -> WorkOrder:
    try:
        return orch.record_running_hours(work_order_id, body.hours)
    except KeyError as exc:
        raise not_found(str(exc))


@router.post("/{work_order_id}/faults", response_model=WorkOrder)
def add_fault(
    work_order_id: str,
    body: FaultIn,
    orch: ServiceOrchestrator = Depends(get_orchestrator),
) -> WorkOrder:
    try:
        return orch.add_fault(work_order_id, body.code, body.description)
    except KeyError as exc:
        raise not_found(str(exc))


@router.post("/{work_order_id}/replace-part", response_model=WorkOrder)
def replace_part(
    work_order_id: str,
    body: ReplacePartIn,
    orch: ServiceOrchestrator = Depends(get_orchestrator),
) -> WorkOrder:
    try:
        return orch.replace_part(work_order_id, body.reservation_id)
    except KeyError as exc:
        raise not_found(str(exc))


@router.post("/{work_order_id}/signature", response_model=WorkOrder)
def capture_signature(
    work_order_id: str,
    body: SignatureIn,
    orch: ServiceOrchestrator = Depends(get_orchestrator),
) -> WorkOrder:
    try:
        return orch.capture_signature(work_order_id, body.signature)
    except KeyError as exc:
        raise not_found(str(exc))


@router.post("/{work_order_id}/close", response_model=Invoice)
def close_work_order(
    work_order_id: str,
    body: CloseWorkOrderIn,
    orch: ServiceOrchestrator = Depends(get_orchestrator),
) -> Invoice:
    """Close the work order and generate its invoice."""
    try:
        return orch.close_work_order(
            work_order_id,
            labor_hours=body.labor_hours,
            summary=body.summary,
        )
    except KeyError as exc:
        raise not_found(str(exc))
