"""Billing engine.

Produces an invoice when a work order closes: parts consumed plus labor, with
lines zeroed out where an active contract covers them. Whether the invoice is
billable at all depends on the coverage returned by the contract manager.
"""

from __future__ import annotations

from ..models import Invoice, InvoiceLine, WorkOrder
from ..store import InMemoryStore
from .contracts import ContractManager

# Standard labor rate charged per hour for billable work.
LABOR_RATE_PER_HOUR = 85.0


class BillingEngine:
    def __init__(self, store: InMemoryStore, contracts: ContractManager) -> None:
        self.store = store
        self.contracts = contracts

    def generate_invoice(self, work_order: WorkOrder) -> Invoice:
        """Build and store an invoice for a closed work order."""
        coverage = self.contracts.coverage(
            work_order.customer_id, work_order.generator_id
        )

        lines: list[InvoiceLine] = []
        parts_total = 0.0
        labor_total = 0.0

        # Parts consumed on this work order.
        for res_id in work_order.reservation_ids:
            reservation = self.store.reservations.get(res_id)
            if reservation is None or not reservation.consumed:
                continue
            part = self.store.parts.get(reservation.part_id)
            if part is None:
                continue
            amount = part.unit_price * reservation.quantity
            covered = coverage.covers_parts
            lines.append(
                InvoiceLine(
                    description=f"{part.name} x{reservation.quantity}",
                    quantity=reservation.quantity,
                    unit_price=part.unit_price,
                    amount=0.0 if covered else amount,
                    covered=covered,
                    coverage_note=(
                        f"Covered by {coverage.contract_type.value}"
                        if covered and coverage.contract_type
                        else ""
                    ),
                )
            )
            if not covered:
                parts_total += amount

        # Labor line.
        if work_order.labor_hours > 0:
            labor_amount = work_order.labor_hours * LABOR_RATE_PER_HOUR
            covered = coverage.covers_labor
            lines.append(
                InvoiceLine(
                    description=f"Labor ({work_order.labor_hours:.1f}h @ "
                    f"{LABOR_RATE_PER_HOUR:.0f}/h)",
                    quantity=work_order.labor_hours,
                    unit_price=LABOR_RATE_PER_HOUR,
                    amount=0.0 if covered else labor_amount,
                    covered=covered,
                    coverage_note=(
                        f"Covered by {coverage.contract_type.value}"
                        if covered and coverage.contract_type
                        else ""
                    ),
                )
            )
            if not covered:
                labor_total += labor_amount

        total = round(parts_total + labor_total, 2)
        invoice = Invoice(
            id=self.store.next_id("INV"),
            work_order_id=work_order.id,
            customer_id=work_order.customer_id,
            lines=lines,
            parts_total=round(parts_total, 2),
            labor_total=round(labor_total, 2),
            total=total,
            billable=total > 0,
            contract_id=coverage.contract_id,
        )
        self.store.invoices[invoice.id] = invoice
        work_order.invoice_id = invoice.id
        return invoice
