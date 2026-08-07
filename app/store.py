"""In-memory data store for the orchestration framework.

A set of dict-backed repositories that hold all runtime state. There is no
external database; the store is seeded at startup (see :mod:`app.seed`) and lives
for the lifetime of the process. Tests build a fresh store per test for isolation.
"""

from __future__ import annotations

import itertools
from typing import Dict, List, Optional

from .models import (
    Contract,
    Customer,
    Generator,
    Incident,
    Invoice,
    PartReservation,
    PurchaseRequest,
    SparePart,
    Technician,
    WorkOrder,
)


class InMemoryStore:
    """Holds every entity in dictionaries keyed by id.

    Ids are generated with per-prefix counters so seed data and runtime data
    share a predictable, human-readable scheme (e.g. ``WO-000004``).
    """

    def __init__(self) -> None:
        self.customers: Dict[str, Customer] = {}
        self.generators: Dict[str, Generator] = {}
        self.technicians: Dict[str, Technician] = {}
        self.parts: Dict[str, SparePart] = {}
        self.contracts: Dict[str, Contract] = {}
        self.work_orders: Dict[str, WorkOrder] = {}
        self.reservations: Dict[str, PartReservation] = {}
        self.purchase_requests: Dict[str, PurchaseRequest] = {}
        self.incidents: Dict[str, Incident] = {}
        self.invoices: Dict[str, Invoice] = {}
        self.logs: List[str] = []
        self._counters: Dict[str, itertools.count] = {}

    # -- id generation ------------------------------------------------------

    def next_id(self, prefix: str) -> str:
        """Return the next sequential id for a prefix, e.g. ``WO-000004``."""
        counter = self._counters.setdefault(prefix, itertools.count(1))
        return f"{prefix}-{next(counter):06d}"

    # -- logging ------------------------------------------------------------

    def log(self, message: str) -> None:
        """Append an operational log line (used for customer notifications)."""
        self.logs.append(message)

    # -- convenience lookups ------------------------------------------------

    def parts_by_category(self, category) -> List[SparePart]:
        """All stocked parts of a given category, most-available first."""
        matches = [p for p in self.parts.values() if p.category == category]
        return sorted(matches, key=lambda p: p.available, reverse=True)

    def contracts_for_customer(self, customer_id: str) -> List[Contract]:
        return [c for c in self.contracts.values() if c.customer_id == customer_id]

    def work_orders_for_generator(self, generator_id: str) -> List[WorkOrder]:
        return [
            w for w in self.work_orders.values() if w.generator_id == generator_id
        ]

    def require_customer(self, customer_id: str) -> Customer:
        customer = self.customers.get(customer_id)
        if customer is None:
            raise KeyError(f"Unknown customer: {customer_id}")
        return customer

    def require_generator(self, generator_id: str) -> Generator:
        generator = self.generators.get(generator_id)
        if generator is None:
            raise KeyError(f"Unknown generator: {generator_id}")
        return generator

    def require_work_order(self, work_order_id: str) -> WorkOrder:
        work_order = self.work_orders.get(work_order_id)
        if work_order is None:
            raise KeyError(f"Unknown work order: {work_order_id}")
        return work_order


# A module-level default store used by the running application. Tests construct
# their own InMemoryStore instances instead of relying on this one.
_store: Optional[InMemoryStore] = None


def get_store() -> InMemoryStore:
    """Return the process-wide store, creating an empty one on first use."""
    global _store
    if _store is None:
        _store = InMemoryStore()
    return _store


def set_store(store: InMemoryStore) -> None:
    """Replace the process-wide store (used by app startup and tests)."""
    global _store
    _store = store
