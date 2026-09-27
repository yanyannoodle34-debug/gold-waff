"""Service orchestrator.

The central coordinator. It composes the specialized engines (dispatch,
inventory, contracts, billing, maintenance, predictive) into the cross-cutting
workflows a generator service company runs:

* customer / asset registration
* emergency breakdown  (report -> incident -> classify -> cover -> dispatch ->
  reserve parts -> notify)
* general service request
* preventive-maintenance scheduling (daily scheduler)
* field-technician transitions and work-order close -> invoice
"""

from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from .engines.billing import BillingEngine
from .engines.contracts import ContractManager
from .engines.dispatch import DispatchEngine
from .engines.inventory import InventoryOrchestrator, ReservationResult
from .engines.maintenance import MaintenanceScheduler
from .engines.predictive import PredictiveMaintenance
from .models import (
    Coverage,
    FaultRecord,
    Incident,
    Invoice,
    MaintenanceRecommendation,
    Priority,
    RequiredPart,
    SensorReading,
    ServiceHistoryEntry,
    Technician,
    WorkOrder,
    WorkOrderStatus,
    WorkOrderType,
    utcnow,
)
from .store import InMemoryStore


class DispatchResult:
    """Bundle returned by workflows that create and dispatch a work order."""

    def __init__(
        self,
        work_order: WorkOrder,
        technician: Optional[Technician],
        reservation: ReservationResult,
        coverage: Coverage,
        incident: Optional[Incident] = None,
    ) -> None:
        self.work_order = work_order
        self.technician = technician
        self.reservation = reservation
        self.coverage = coverage
        self.incident = incident


class ServiceOrchestrator:
    def __init__(self, store: InMemoryStore) -> None:
        self.store = store
        self.contracts = ContractManager(store)
        self.dispatch = DispatchEngine(store)
        self.inventory = InventoryOrchestrator(store)
        self.maintenance = MaintenanceScheduler(store)
        self.billing = BillingEngine(store, self.contracts)
        self.predictive = PredictiveMaintenance()

    # -- work-order creation & dispatch ------------------------------------

    def create_work_order(
        self,
        generator_id: str,
        work_order_type: WorkOrderType,
        priority: Priority = Priority.NORMAL,
        required_parts: Optional[List[RequiredPart]] = None,
        incident_id: Optional[str] = None,
        scheduled_date: Optional[datetime] = None,
        auto_dispatch: bool = True,
    ) -> DispatchResult:
        """Create a work order, check coverage, dispatch a tech, reserve parts.

        This is the shared core behind both service requests and emergency
        breakdowns. When ``auto_dispatch`` is true a technician is selected and
        the required parts are reserved immediately.
        """
        generator = self.store.require_generator(generator_id)
        customer = self.store.require_customer(generator.customer_id)

        work_order = WorkOrder(
            id=self.store.next_id("WO"),
            generator_id=generator.id,
            customer_id=customer.id,
            type=work_order_type,
            priority=priority,
            required_parts=required_parts or [],
            incident_id=incident_id,
            scheduled_date=scheduled_date,
        )
        self.store.work_orders[work_order.id] = work_order

        coverage = self.contracts.coverage(customer.id, generator.id)
        self.store.log(
            f"[Orchestrator] Work order {work_order.id} created for "
            f"{generator.serial_number} ({work_order_type.value}); "
            + (
                f"covered by {coverage.contract_type.value}"
                if coverage.is_covered and coverage.contract_type
                else "no contract coverage (billable)"
            )
        )

        technician: Optional[Technician] = None
        reservation = ReservationResult()
        if auto_dispatch:
            technician = self._assign_technician(work_order, generator)
            reservation = self._reserve_parts(work_order)

        self.store.log(
            f"[Notification] Customer {customer.name} notified about work order "
            f"{work_order.id}"
        )
        return DispatchResult(
            work_order, technician, reservation, coverage, None
        )

    def _assign_technician(
        self, work_order: WorkOrder, generator
    ) -> Optional[Technician]:
        technician = self.dispatch.select_technician(work_order, generator)
        if technician is not None:
            work_order.assigned_technician_id = technician.id
            work_order.status = WorkOrderStatus.ASSIGNED
            technician.current_workload += 1
            self.store.log(
                f"[Dispatch] {technician.name} assigned to {work_order.id}"
            )
        else:
            self.store.log(
                f"[Dispatch] No qualified technician available for "
                f"{work_order.id}; escalated"
            )
        return technician

    def _reserve_parts(self, work_order: WorkOrder) -> ReservationResult:
        if not work_order.required_parts:
            return ReservationResult()
        result = self.inventory.reserve(work_order.id, work_order.required_parts)
        work_order.reservation_ids.extend(r.id for r in result.reservations)
        work_order.purchase_request_ids.extend(
            pr.id for pr in result.purchase_requests
        )
        if result.reservations and work_order.status == WorkOrderStatus.ASSIGNED:
            work_order.status = WorkOrderStatus.PARTS_RESERVED
        return result

    # -- emergency breakdown -----------------------------------------------

    def report_breakdown(
        self,
        generator_id: str,
        description: str,
        priority: Priority = Priority.EMERGENCY,
        required_parts: Optional[List[RequiredPart]] = None,
    ) -> DispatchResult:
        """Full emergency-breakdown workflow, from incident to dispatch."""
        generator = self.store.require_generator(generator_id)
        incident = Incident(
            id=self.store.next_id("INC"),
            customer_id=generator.customer_id,
            generator_id=generator.id,
            description=description,
            priority=priority,
        )
        self.store.incidents[incident.id] = incident
        self.store.log(
            f"[Incident] {incident.id} raised for {generator.serial_number} "
            f"(priority {priority.value})"
        )

        result = self.create_work_order(
            generator_id=generator_id,
            work_order_type=WorkOrderType.BREAKDOWN,
            priority=priority,
            required_parts=required_parts,
            incident_id=incident.id,
        )
        incident.work_order_id = result.work_order.id
        result.incident = incident
        return result

    def create_service_request(
        self,
        generator_id: str,
        work_order_type: WorkOrderType,
        priority: Priority = Priority.NORMAL,
        required_parts: Optional[List[RequiredPart]] = None,
        scheduled_date: Optional[datetime] = None,
    ) -> DispatchResult:
        """A non-emergency customer service request."""
        return self.create_work_order(
            generator_id=generator_id,
            work_order_type=work_order_type,
            priority=priority,
            required_parts=required_parts,
            scheduled_date=scheduled_date,
        )

    # -- preventive maintenance (daily scheduler) --------------------------

    def schedule_preventive_maintenance(self) -> List[DispatchResult]:
        """Generate and dispatch PM work orders for every generator due."""
        results: List[DispatchResult] = []
        for generator in self.maintenance.generators_due():
            # Skip generators that already have an open PM work order.
            if self._has_open_pm(generator.id):
                continue
            result = self.create_work_order(
                generator_id=generator.id,
                work_order_type=WorkOrderType.PREVENTIVE,
                priority=Priority.NORMAL,
                required_parts=self.maintenance.standard_pm_parts(),
                scheduled_date=utcnow(),
            )
            results.append(result)
        self.store.log(
            f"[Scheduler] Daily run generated {len(results)} PM work order(s)"
        )
        return results

    def _has_open_pm(self, generator_id: str) -> bool:
        for wo in self.store.work_orders_for_generator(generator_id):
            if (
                wo.type == WorkOrderType.PREVENTIVE
                and wo.status != WorkOrderStatus.CLOSED
                and wo.status != WorkOrderStatus.CANCELLED
            ):
                return True
        return False

    # -- field-technician transitions --------------------------------------

    def record_running_hours(self, work_order_id: str, hours: float) -> WorkOrder:
        wo = self.store.require_work_order(work_order_id)
        wo.running_hours_recorded = hours
        generator = self.store.require_generator(wo.generator_id)
        generator.running_hours = max(generator.running_hours, hours)
        if wo.status in (WorkOrderStatus.ASSIGNED, WorkOrderStatus.PARTS_RESERVED):
            wo.status = WorkOrderStatus.ON_SITE
        return wo

    def add_fault(self, work_order_id: str, code: str, description: str) -> WorkOrder:
        wo = self.store.require_work_order(work_order_id)
        wo.faults.append(FaultRecord(code=code, description=description))
        wo.status = WorkOrderStatus.IN_PROGRESS
        return wo

    def replace_part(self, work_order_id: str, reservation_id: str) -> WorkOrder:
        """Mark a reserved part as fitted (consumes it from stock)."""
        wo = self.store.require_work_order(work_order_id)
        reservation = self.store.reservations.get(reservation_id)
        if reservation is None or reservation.work_order_id != wo.id:
            raise KeyError(f"Reservation {reservation_id} not on {wo.id}")
        self.inventory.consume(reservation)
        wo.status = WorkOrderStatus.IN_PROGRESS
        return wo

    def capture_signature(self, work_order_id: str, signature: str) -> WorkOrder:
        wo = self.store.require_work_order(work_order_id)
        wo.customer_signature = signature
        wo.status = WorkOrderStatus.AWAITING_SIGNOFF
        return wo

    def close_work_order(
        self,
        work_order_id: str,
        labor_hours: float = 0.0,
        consume_remaining_parts: bool = True,
        summary: str = "",
    ) -> Invoice:
        """Close a work order: consume parts, update history, invoice.

        Any reserved-but-not-yet-fitted parts are consumed on close by default
        (they were used on the job). The generator's service history and running
        hours are updated, then the billing engine produces the invoice.
        """
        wo = self.store.require_work_order(work_order_id)
        wo.labor_hours = labor_hours

        if consume_remaining_parts:
            for res_id in wo.reservation_ids:
                reservation = self.store.reservations.get(res_id)
                if reservation is not None and not reservation.consumed:
                    self.inventory.consume(reservation)

        generator = self.store.require_generator(wo.generator_id)
        performed_hours = (
            wo.running_hours_recorded
            if wo.running_hours_recorded is not None
            else generator.running_hours
        )
        generator.service_history.append(
            ServiceHistoryEntry(
                work_order_id=wo.id,
                type=wo.type,
                performed_at=utcnow(),
                running_hours=performed_hours,
                technician_id=wo.assigned_technician_id,
                summary=summary or f"{wo.type.value} completed",
            )
        )
        # Preventive maintenance resets the PM interval baseline.
        if wo.type == WorkOrderType.PREVENTIVE:
            generator.last_pm_hours = performed_hours

        wo.status = WorkOrderStatus.CLOSED
        wo.closed_at = utcnow()

        # Free the assigned technician.
        if wo.assigned_technician_id:
            tech = self.store.technicians.get(wo.assigned_technician_id)
            if tech is not None and tech.current_workload > 0:
                tech.current_workload -= 1

        invoice = self.billing.generate_invoice(wo)
        self.store.log(
            f"[Billing] Invoice {invoice.id} for {wo.id}: total {invoice.total} "
            + ("(billable)" if invoice.billable else "(fully covered)")
        )
        return invoice

    # -- predictive maintenance --------------------------------------------

    def ingest_reading(
        self, generator_id: str, reading: SensorReading
    ) -> List[MaintenanceRecommendation]:
        """Feed a sensor reading to analytics and return recommendations."""
        generator = self.store.require_generator(generator_id)
        if reading.running_hours is not None:
            generator.running_hours = max(
                generator.running_hours, reading.running_hours
            )
        recommendations = self.predictive.analyze(generator, reading)
        for rec in recommendations:
            self.store.log(
                f"[Predictive] {generator.serial_number}: {rec.reason} -> "
                f"{rec.recommended_action.value}"
            )
        return recommendations
