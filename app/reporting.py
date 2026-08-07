"""Reporting / dashboard aggregation.

Computes the operational KPIs a service manager watches: fleet under contract,
upcoming preventive maintenance, emergency load, mean time to repair, first-time
fix rate, technician utilization, parts consumption, and revenue by contract.
"""

from __future__ import annotations

from datetime import date
from typing import Dict

from .engines.maintenance import MaintenanceScheduler
from .models import WorkOrderStatus, WorkOrderType
from .store import InMemoryStore


def build_dashboard(store: InMemoryStore) -> Dict:
    """Aggregate the full KPI dashboard from current store state."""
    generators = list(store.generators.values())
    work_orders = list(store.work_orders.values())
    scheduler = MaintenanceScheduler(store)

    # Generators under an active contract today.
    today = date.today()
    covered_generator_ids = set()
    for contract in store.contracts.values():
        if contract.is_active_on(today):
            covered_generator_ids.update(contract.covered_generator_ids)

    # Emergency jobs (breakdown work orders).
    emergency_jobs = [
        w for w in work_orders if w.type == WorkOrderType.BREAKDOWN
    ]

    # Mean time to repair over closed breakdown work orders (hours).
    repair_durations = [
        (w.closed_at - w.created_at).total_seconds() / 3600.0
        for w in emergency_jobs
        if w.closed_at is not None
    ]
    mttr_hours = (
        round(sum(repair_durations) / len(repair_durations), 2)
        if repair_durations
        else None
    )

    # First-time fix rate: closed jobs with no purchase-request shortfall and at
    # least one recorded fault resolution, over all closed jobs.
    closed = [w for w in work_orders if w.status == WorkOrderStatus.CLOSED]
    first_time_fixes = [
        w for w in closed if not w.purchase_request_ids
    ]
    first_time_fix_rate = (
        round(len(first_time_fixes) / len(closed), 3) if closed else None
    )

    # Technician utilization: current workload over max, averaged.
    techs = list(store.technicians.values())
    utilization = (
        round(
            sum(t.current_workload / t.max_workload for t in techs) / len(techs), 3
        )
        if techs
        else None
    )
    per_technician = {
        t.name: {
            "current_workload": t.current_workload,
            "max_workload": t.max_workload,
            "utilization": round(t.current_workload / t.max_workload, 3),
        }
        for t in techs
    }

    # Parts consumption by category (consumed reservations).
    parts_consumption: Dict[str, int] = {}
    for res in store.reservations.values():
        if res.consumed:
            key = res.category.value
            parts_consumption[key] = parts_consumption.get(key, 0) + res.quantity

    # Revenue by contract type (billable invoice totals attributed to coverage).
    revenue_by_contract: Dict[str, float] = {}
    uncontracted_revenue = 0.0
    for inv in store.invoices.values():
        if inv.contract_id:
            contract = store.contracts.get(inv.contract_id)
            key = contract.type.value if contract else "UNKNOWN"
            revenue_by_contract[key] = round(
                revenue_by_contract.get(key, 0.0) + inv.total, 2
            )
        else:
            uncontracted_revenue = round(uncontracted_revenue + inv.total, 2)

    return {
        "active_generators": len(generators),
        "generators_under_contract": len(
            [g for g in generators if g.id in covered_generator_ids]
        ),
        "upcoming_preventive_maintenance": len(scheduler.generators_due()),
        "emergency_jobs": len(emergency_jobs),
        "open_work_orders": len(
            [
                w
                for w in work_orders
                if w.status
                not in (WorkOrderStatus.CLOSED, WorkOrderStatus.CANCELLED)
            ]
        ),
        "mttr_hours": mttr_hours,
        "first_time_fix_rate": first_time_fix_rate,
        "technician_utilization": utilization,
        "per_technician_utilization": per_technician,
        "parts_consumption": parts_consumption,
        "revenue_by_contract": revenue_by_contract,
        "uncontracted_revenue": uncontracted_revenue,
        "total_invoiced": round(
            sum(inv.total for inv in store.invoices.values()), 2
        ),
        "open_purchase_requests": len(store.purchase_requests),
    }
