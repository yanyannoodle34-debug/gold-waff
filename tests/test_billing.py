"""Billing engine: coverage applied to parts and labor at close."""

from __future__ import annotations

from app.models import PartCategory, Priority, RequiredPart, WorkOrderType


def test_cmc_invoice_fully_covered(orch, store):
    # GEN-000001 is under a CMC contract (parts + labor covered).
    result = orch.create_service_request(
        generator_id="GEN-000001",
        work_order_type=WorkOrderType.OIL_CHANGE,
        required_parts=[RequiredPart(category=PartCategory.ENGINE_OIL, quantity=1)],
    )
    invoice = orch.close_work_order(result.work_order.id, labor_hours=2.0)
    assert invoice.total == 0.0
    assert invoice.billable is False
    assert all(line.covered for line in invoice.lines)


def test_amc_labor_covered_parts_billable(orch, store):
    # GEN-000003 is under an AMC (labor covered, parts billable).
    result = orch.create_service_request(
        generator_id="GEN-000003",
        work_order_type=WorkOrderType.FILTER_REPLACEMENT,
        required_parts=[RequiredPart(category=PartCategory.OIL_FILTER, quantity=1)],
    )
    invoice = orch.close_work_order(result.work_order.id, labor_hours=1.0)
    assert invoice.labor_total == 0.0  # labor covered
    assert invoice.parts_total > 0.0  # parts billable
    assert invoice.billable is True


def test_uncovered_generator_fully_billable(orch, store):
    # GEN-000004 has no contract: both parts and labor are charged.
    result = orch.create_service_request(
        generator_id="GEN-000004",
        work_order_type=WorkOrderType.INSPECTION,
        required_parts=[RequiredPart(category=PartCategory.AIR_FILTER, quantity=1)],
    )
    invoice = orch.close_work_order(result.work_order.id, labor_hours=3.0)
    assert invoice.parts_total > 0.0
    assert invoice.labor_total > 0.0
    assert invoice.total == invoice.parts_total + invoice.labor_total
    assert invoice.billable is True
