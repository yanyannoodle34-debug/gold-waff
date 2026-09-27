"""Dispatch engine.

Selects the best technician for a work order by scoring every available,
qualified technician on skills, certifications, proximity to the generator, and
current workload, with an emergency boost so critical jobs pull in the nearest
capable technician.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Dict, List, Optional

from ..models import Generator, Priority, Technician, WorkOrder, WorkOrderType
from ..store import InMemoryStore

# Skills a work order type requires a technician to hold.
REQUIRED_SKILLS: Dict[WorkOrderType, List[str]] = {
    WorkOrderType.PREVENTIVE: ["mechanical"],
    WorkOrderType.BREAKDOWN: ["mechanical", "electrical"],
    WorkOrderType.INSPECTION: ["mechanical"],
    WorkOrderType.OVERHAUL: ["mechanical", "engine"],
    WorkOrderType.LOAD_BANK: ["electrical", "load_testing"],
    WorkOrderType.OIL_CHANGE: ["mechanical"],
    WorkOrderType.FILTER_REPLACEMENT: ["mechanical"],
}


@dataclass
class DispatchCandidate:
    """A scored technician considered for a work order."""

    technician: Technician
    score: float
    distance_km: float


def haversine_km(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    """Great-circle distance between two points in kilometers."""
    radius = 6371.0
    d_lat = math.radians(lat2 - lat1)
    d_lng = math.radians(lng2 - lng1)
    a = (
        math.sin(d_lat / 2) ** 2
        + math.cos(math.radians(lat1))
        * math.cos(math.radians(lat2))
        * math.sin(d_lng / 2) ** 2
    )
    return radius * 2 * math.asin(math.sqrt(a))


class DispatchEngine:
    def __init__(self, store: InMemoryStore) -> None:
        self.store = store

    def required_skills(self, work_order_type: WorkOrderType) -> List[str]:
        return REQUIRED_SKILLS.get(work_order_type, ["mechanical"])

    def rank_candidates(
        self, work_order: WorkOrder, generator: Generator
    ) -> List[DispatchCandidate]:
        """Return qualified technicians ranked best-first for a work order."""
        needed = set(self.required_skills(work_order.type))
        candidates: List[DispatchCandidate] = []

        for tech in self.store.technicians.values():
            if not tech.is_available:
                continue
            if tech.current_workload >= tech.max_workload:
                continue
            if not needed.issubset(set(tech.skills)):
                continue

            distance = haversine_km(
                tech.location.lat,
                tech.location.lng,
                generator.location.lat,
                generator.location.lng,
            )
            candidates.append(
                DispatchCandidate(
                    technician=tech,
                    score=self._score(tech, work_order, generator, distance),
                    distance_km=round(distance, 1),
                )
            )

        candidates.sort(key=lambda c: c.score, reverse=True)
        return candidates

    def select_technician(
        self, work_order: WorkOrder, generator: Generator
    ) -> Optional[Technician]:
        """Pick the single best technician, or ``None`` if none qualify."""
        ranked = self.rank_candidates(work_order, generator)
        return ranked[0].technician if ranked else None

    def _score(
        self,
        tech: Technician,
        work_order: WorkOrder,
        generator: Generator,
        distance_km: float,
    ) -> float:
        """Weighted score: closeness + spare capacity + certification bonus.

        Emergency work orders weight proximity far more heavily so the nearest
        capable technician wins.
        """
        # Proximity component: 1.0 next door, decaying with distance.
        proximity = 1.0 / (1.0 + distance_km / 25.0)

        # Spare-capacity component: prefer less-loaded technicians.
        capacity = (tech.max_workload - tech.current_workload) / tech.max_workload

        # Certification bonus: reward relevant certifications.
        cert_bonus = 0.1 * len(tech.certifications)

        proximity_weight = 4.0 if work_order.priority == Priority.EMERGENCY else 2.0
        return proximity_weight * proximity + 1.0 * capacity + cert_bonus
