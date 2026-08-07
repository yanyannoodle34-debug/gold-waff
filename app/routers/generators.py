"""Generator asset registration, lookup, and service history."""

from __future__ import annotations

from datetime import date
from typing import List, Optional

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from ..deps import get_orchestrator, not_found
from ..models import (
    Generator,
    GeoLocation,
    MaintenanceRecommendation,
    SensorReading,
    ServiceHistoryEntry,
)
from ..orchestrator import ServiceOrchestrator
from ..store import get_store

router = APIRouter(prefix="/generators", tags=["Generators"])


class GeneratorIn(BaseModel):
    customer_id: str
    serial_number: str
    model: str
    engine: str
    alternator: str
    controller: str
    installation_date: date
    running_hours: float = 0.0
    location: GeoLocation
    warranty_until: Optional[date] = None
    last_pm_hours: float = 0.0
    pm_interval_hours: float = 250.0


@router.get("", response_model=List[Generator])
def list_generators() -> List[Generator]:
    return list(get_store().generators.values())


@router.post("", response_model=Generator, status_code=201)
def register_generator(body: GeneratorIn) -> Generator:
    store = get_store()
    if body.customer_id not in store.customers:
        raise not_found(f"Unknown customer: {body.customer_id}")
    generator = Generator(id=store.next_id("GEN"), **body.model_dump())
    store.generators[generator.id] = generator
    store.log(
        f"[Asset] Registered generator {generator.serial_number} ({generator.id})"
    )
    return generator


@router.get("/{generator_id}", response_model=Generator)
def get_generator(generator_id: str) -> Generator:
    generator = get_store().generators.get(generator_id)
    if generator is None:
        raise not_found(f"Unknown generator: {generator_id}")
    return generator


@router.get("/{generator_id}/history", response_model=List[ServiceHistoryEntry])
def get_history(generator_id: str) -> List[ServiceHistoryEntry]:
    generator = get_store().generators.get(generator_id)
    if generator is None:
        raise not_found(f"Unknown generator: {generator_id}")
    return generator.service_history


@router.post(
    "/{generator_id}/readings",
    response_model=List[MaintenanceRecommendation],
    tags=["Predictive Maintenance"],
)
def ingest_reading(
    generator_id: str,
    reading: SensorReading,
    orch: ServiceOrchestrator = Depends(get_orchestrator),
) -> List[MaintenanceRecommendation]:
    """Submit an IoT sensor reading; returns predictive recommendations."""
    try:
        return orch.ingest_reading(generator_id, reading)
    except KeyError as exc:
        raise not_found(str(exc))
