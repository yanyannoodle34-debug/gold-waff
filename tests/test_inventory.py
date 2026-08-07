"""Inventory orchestrator: reservation, purchase requests, and consumption."""

from __future__ import annotations

from app.models import PartCategory, RequiredPart


def _part_of(store, category):
    return next(p for p in store.parts.values() if p.category == category)


def test_reserve_available_part(orch, store):
    oil = _part_of(store, PartCategory.ENGINE_OIL)
    before = oil.available
    result = orch.inventory.reserve(
        "WO-TEST", [RequiredPart(category=PartCategory.ENGINE_OIL, quantity=2)]
    )
    assert result.fully_reserved
    assert len(result.reservations) == 1
    assert oil.reserved == 2
    assert oil.available == before - 2


def test_shortfall_raises_purchase_request(orch, store):
    # Only 2 batteries on hand; request 5 -> partial reserve + purchase request.
    battery = _part_of(store, PartCategory.BATTERY)
    result = orch.inventory.reserve(
        "WO-TEST", [RequiredPart(category=PartCategory.BATTERY, quantity=5)]
    )
    assert not result.fully_reserved
    assert battery.reserved == 2
    assert len(result.purchase_requests) == 1
    assert result.purchase_requests[0].quantity == 3


def test_consume_decrements_on_hand(orch, store):
    oil = _part_of(store, PartCategory.ENGINE_OIL)
    on_hand_before = oil.on_hand
    result = orch.inventory.reserve(
        "WO-TEST", [RequiredPart(category=PartCategory.ENGINE_OIL, quantity=1)]
    )
    orch.inventory.consume(result.reservations[0])
    assert oil.on_hand == on_hand_before - 1
    assert oil.reserved == 0


def test_release_returns_stock(orch, store):
    oil = _part_of(store, PartCategory.ENGINE_OIL)
    result = orch.inventory.reserve(
        "WO-TEST", [RequiredPart(category=PartCategory.ENGINE_OIL, quantity=3)]
    )
    assert oil.reserved == 3
    orch.inventory.release(result.reservations[0])
    assert oil.reserved == 0
