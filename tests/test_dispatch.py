"""Dispatch engine: qualification filtering, proximity, and emergency boost."""

from __future__ import annotations

from app.engines.dispatch import haversine_km
from app.models import Priority, WorkOrder, WorkOrderType


def _probe(store, generator_id: str, wo_type, priority) -> WorkOrder:
    generator = store.generators[generator_id]
    return WorkOrder(
        id="PROBE",
        generator_id=generator.id,
        customer_id=generator.customer_id,
        type=wo_type,
        priority=priority,
    )


def test_haversine_known_distance():
    # Deira (~25.27,55.31) to Jebel Ali (~24.98,55.06) is roughly 40 km.
    d = haversine_km(25.271, 55.307, 24.985, 55.061)
    assert 30 < d < 55


def test_load_bank_requires_specialist_skill(orch, store):
    # Vikram (TEC-000003) only has "mechanical" and cannot do load-bank testing.
    probe = _probe(store, "GEN-000005", WorkOrderType.LOAD_BANK, Priority.NORMAL)
    generator = store.generators["GEN-000005"]
    ranked = orch.dispatch.rank_candidates(probe, generator)
    ids = {c.technician.id for c in ranked}
    assert "TEC-000003" not in ids
    # Rashid and Lena both have load_testing.
    assert {"TEC-000001", "TEC-000004"}.issubset(ids)


def test_emergency_prefers_nearest_qualified(orch, store):
    # Breakdown on GEN-000001 in Silicon Oasis; Rashid (TEC-000001) is nearest.
    probe = _probe(store, "GEN-000001", WorkOrderType.BREAKDOWN, Priority.EMERGENCY)
    generator = store.generators["GEN-000001"]
    best = orch.dispatch.select_technician(probe, generator)
    assert best is not None
    assert best.id == "TEC-000001"


def test_unavailable_and_full_technicians_excluded(orch, store):
    tech = store.technicians["TEC-000002"]
    tech.is_available = False
    probe = _probe(store, "GEN-000003", WorkOrderType.INSPECTION, Priority.NORMAL)
    generator = store.generators["GEN-000003"]
    ranked = orch.dispatch.rank_candidates(probe, generator)
    assert "TEC-000002" not in {c.technician.id for c in ranked}
