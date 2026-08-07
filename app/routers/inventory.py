"""Inventory: list stock, reservations, and purchase requests."""

from __future__ import annotations

from typing import List

from fastapi import APIRouter

from ..models import PartReservation, PurchaseRequest, SparePart
from ..store import get_store

router = APIRouter(prefix="/inventory", tags=["Inventory"])


@router.get("/parts", response_model=List[SparePart])
def list_parts() -> List[SparePart]:
    return list(get_store().parts.values())


@router.get("/parts/below-reorder", response_model=List[SparePart])
def list_below_reorder() -> List[SparePart]:
    """Parts whose available stock is at or below the reorder level."""
    return [
        p
        for p in get_store().parts.values()
        if p.available <= p.reorder_level
    ]


@router.get("/reservations", response_model=List[PartReservation])
def list_reservations() -> List[PartReservation]:
    return list(get_store().reservations.values())


@router.get("/purchase-requests", response_model=List[PurchaseRequest])
def list_purchase_requests() -> List[PurchaseRequest]:
    return list(get_store().purchase_requests.values())
