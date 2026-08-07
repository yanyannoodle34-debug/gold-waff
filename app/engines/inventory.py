"""Inventory orchestrator.

Reserves spare parts for a work order when stock is available and raises a
purchase request when it is not. Consumes reservations at work-order close,
decrementing on-hand stock.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List

from ..models import PartReservation, PurchaseRequest, RequiredPart
from ..store import InMemoryStore


@dataclass
class ReservationResult:
    """Outcome of reserving the parts required by a work order."""

    reservations: List[PartReservation] = field(default_factory=list)
    purchase_requests: List[PurchaseRequest] = field(default_factory=list)

    @property
    def fully_reserved(self) -> bool:
        return not self.purchase_requests


class InventoryOrchestrator:
    def __init__(self, store: InMemoryStore) -> None:
        self.store = store

    def reserve(
        self, work_order_id: str, required: List[RequiredPart]
    ) -> ReservationResult:
        """Reserve each required part, raising purchase requests for shortfalls.

        A required quantity is filled from the best-stocked part in its
        category. If no single part can cover it, a purchase request is raised
        for the missing quantity (partial reservations are still made).
        """
        result = ReservationResult()

        for req in required:
            remaining = req.quantity
            for part in self.store.parts_by_category(req.category):
                if remaining <= 0:
                    break
                take = min(part.available, remaining)
                if take <= 0:
                    continue
                part.reserved += take
                reservation = PartReservation(
                    id=self.store.next_id("RES"),
                    work_order_id=work_order_id,
                    part_id=part.id,
                    category=req.category,
                    quantity=take,
                )
                self.store.reservations[reservation.id] = reservation
                result.reservations.append(reservation)
                remaining -= take

            if remaining > 0:
                pr = PurchaseRequest(
                    id=self.store.next_id("PR"),
                    work_order_id=work_order_id,
                    category=req.category,
                    quantity=remaining,
                )
                self.store.purchase_requests[pr.id] = pr
                result.purchase_requests.append(pr)
                self.store.log(
                    f"[Inventory] Purchase request {pr.id} raised for "
                    f"{remaining} x {req.category.value}"
                )

        return result

    def consume(self, reservation: PartReservation) -> None:
        """Consume a reservation at close: decrement on-hand and reserved."""
        if reservation.consumed:
            return
        part = self.store.parts.get(reservation.part_id)
        if part is not None:
            part.on_hand = max(0, part.on_hand - reservation.quantity)
            part.reserved = max(0, part.reserved - reservation.quantity)
        reservation.consumed = True

    def release(self, reservation: PartReservation) -> None:
        """Release an unconsumed reservation back to available stock."""
        if reservation.consumed:
            return
        part = self.store.parts.get(reservation.part_id)
        if part is not None:
            part.reserved = max(0, part.reserved - reservation.quantity)
        reservation.consumed = True
