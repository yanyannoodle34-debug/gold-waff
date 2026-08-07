"""Technician roster."""

from __future__ import annotations

from typing import List

from fastapi import APIRouter
from pydantic import BaseModel

from ..deps import not_found
from ..models import GeoLocation, Technician
from ..store import get_store

router = APIRouter(prefix="/technicians", tags=["Technicians"])


class TechnicianIn(BaseModel):
    name: str
    skills: List[str] = []
    certifications: List[str] = []
    location: GeoLocation
    is_available: bool = True
    current_workload: int = 0
    max_workload: int = 5


@router.get("", response_model=List[Technician])
def list_technicians() -> List[Technician]:
    return list(get_store().technicians.values())


@router.post("", response_model=Technician, status_code=201)
def register_technician(body: TechnicianIn) -> Technician:
    store = get_store()
    technician = Technician(id=store.next_id("TEC"), **body.model_dump())
    store.technicians[technician.id] = technician
    store.log(f"[Roster] Added technician {technician.name} ({technician.id})")
    return technician


@router.get("/{technician_id}", response_model=Technician)
def get_technician(technician_id: str) -> Technician:
    technician = get_store().technicians.get(technician_id)
    if technician is None:
        raise not_found(f"Unknown technician: {technician_id}")
    return technician
