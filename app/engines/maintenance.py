"""Maintenance scheduler.

Detects generators due for preventive maintenance (by running-hours interval)
and, via the daily scheduler, turns them into preventive work orders. The
standard PM parts basket (oil + filters) is defined here.
"""

from __future__ import annotations

from typing import List

from ..models import Generator, PartCategory, RequiredPart, WorkOrderType
from ..store import InMemoryStore

# Parts consumed by a routine preventive-maintenance visit.
STANDARD_PM_PARTS: List[RequiredPart] = [
    RequiredPart(category=PartCategory.ENGINE_OIL, quantity=1),
    RequiredPart(category=PartCategory.OIL_FILTER, quantity=1),
    RequiredPart(category=PartCategory.FUEL_FILTER, quantity=1),
    RequiredPart(category=PartCategory.AIR_FILTER, quantity=1),
]


class MaintenanceScheduler:
    def __init__(self, store: InMemoryStore) -> None:
        self.store = store

    def is_due(self, generator: Generator) -> bool:
        """Whether a generator has crossed its PM running-hours interval."""
        return (
            generator.running_hours - generator.last_pm_hours
            >= generator.pm_interval_hours
        )

    def generators_due(self) -> List[Generator]:
        """All generators currently due for preventive maintenance."""
        return [g for g in self.store.generators.values() if self.is_due(g)]

    def standard_pm_parts(self) -> List[RequiredPart]:
        """A fresh copy of the standard PM parts basket."""
        return [RequiredPart(category=p.category, quantity=p.quantity) for p in
                STANDARD_PM_PARTS]

    def pm_work_order_type(self) -> WorkOrderType:
        return WorkOrderType.PREVENTIVE
