"""Domain models for the generator service orchestration framework.

Everything the orchestrator coordinates is defined here as Pydantic models and
enums: customers, generator assets, technicians, spare parts, work orders,
contracts, incidents, invoices, and the supporting value objects.
"""

from __future__ import annotations

from datetime import date, datetime, timezone
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field


def utcnow() -> datetime:
    """Timezone-aware UTC timestamp (replacement for deprecated datetime.utcnow)."""
    return datetime.now(timezone.utc)


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------


class WorkOrderType(str, Enum):
    """The kind of service a work order represents."""

    PREVENTIVE = "PREVENTIVE"
    BREAKDOWN = "BREAKDOWN"
    INSPECTION = "INSPECTION"
    OVERHAUL = "OVERHAUL"
    LOAD_BANK = "LOAD_BANK"
    OIL_CHANGE = "OIL_CHANGE"
    FILTER_REPLACEMENT = "FILTER_REPLACEMENT"


class WorkOrderStatus(str, Enum):
    """Lifecycle of a work order, from creation to close."""

    CREATED = "CREATED"
    ASSIGNED = "ASSIGNED"
    PARTS_RESERVED = "PARTS_RESERVED"
    EN_ROUTE = "EN_ROUTE"
    ON_SITE = "ON_SITE"
    IN_PROGRESS = "IN_PROGRESS"
    TESTING = "TESTING"
    AWAITING_SIGNOFF = "AWAITING_SIGNOFF"
    CLOSED = "CLOSED"
    CANCELLED = "CANCELLED"


class Priority(str, Enum):
    """Priority used by the dispatch engine to rank jobs."""

    EMERGENCY = "EMERGENCY"
    HIGH = "HIGH"
    NORMAL = "NORMAL"
    LOW = "LOW"


class ContractType(str, Enum):
    """Supported service contract types."""

    AMC = "AMC"  # Annual Maintenance Contract: labor covered, parts billable
    CMC = "CMC"  # Comprehensive Maintenance Contract: parts + labor covered
    EMERGENCY_SUPPORT = "EMERGENCY_SUPPORT"  # emergency response only
    RENTAL = "RENTAL"  # rental generator support: everything covered
    WARRANTY = "WARRANTY"  # manufacturer warranty: parts + labor within window


class PartCategory(str, Enum):
    """Categories of spare parts tracked by the inventory orchestrator."""

    ENGINE_OIL = "ENGINE_OIL"
    FUEL_FILTER = "FUEL_FILTER"
    OIL_FILTER = "OIL_FILTER"
    AIR_FILTER = "AIR_FILTER"
    BELT = "BELT"
    BATTERY = "BATTERY"
    AVR = "AVR"
    CONTROLLER = "CONTROLLER"
    SENSOR = "SENSOR"
    INJECTOR = "INJECTOR"


# ---------------------------------------------------------------------------
# Value objects
# ---------------------------------------------------------------------------


class GeoLocation(BaseModel):
    """A latitude/longitude point used for technician-to-site distance."""

    lat: float
    lng: float
    label: str = ""


class ServiceHistoryEntry(BaseModel):
    """A closed work order recorded against a generator's history."""

    work_order_id: str
    type: WorkOrderType
    performed_at: datetime
    running_hours: float
    technician_id: Optional[str] = None
    summary: str = ""


class RequiredPart(BaseModel):
    """A part (by category) and quantity a work order needs."""

    category: PartCategory
    quantity: int = 1


class FaultRecord(BaseModel):
    """A fault logged by a technician on site."""

    code: str
    description: str
    recorded_at: datetime = Field(default_factory=utcnow)


# ---------------------------------------------------------------------------
# Core entities
# ---------------------------------------------------------------------------


class Customer(BaseModel):
    """A customer who owns one or more generators."""

    id: str
    name: str
    contact_name: str = ""
    phone: str = ""
    email: str = ""
    address: str = ""


class Generator(BaseModel):
    """A generator asset with its full digital record."""

    id: str
    customer_id: str
    serial_number: str
    model: str
    engine: str
    alternator: str
    controller: str
    installation_date: date
    running_hours: float = 0.0
    location: GeoLocation
    warranty_until: Optional[date] = None
    service_history: List[ServiceHistoryEntry] = Field(default_factory=list)
    last_pm_hours: float = 0.0
    pm_interval_hours: float = 250.0


class Technician(BaseModel):
    """A field technician available for dispatch."""

    id: str
    name: str
    skills: List[str] = Field(default_factory=list)
    certifications: List[str] = Field(default_factory=list)
    location: GeoLocation
    is_available: bool = True
    current_workload: int = 0
    max_workload: int = 5


class SparePart(BaseModel):
    """A stocked spare part with on-hand and reserved quantities."""

    id: str
    name: str
    category: PartCategory
    on_hand: int = 0
    reserved: int = 0
    reorder_level: int = 0
    unit_price: float = 0.0

    @property
    def available(self) -> int:
        """Quantity that can still be reserved."""
        return self.on_hand - self.reserved


class PartReservation(BaseModel):
    """A reservation of a specific part against a work order."""

    id: str
    work_order_id: str
    part_id: str
    category: PartCategory
    quantity: int
    consumed: bool = False


class PurchaseRequest(BaseModel):
    """Raised when required parts are not available in stock."""

    id: str
    work_order_id: str
    category: PartCategory
    quantity: int
    reason: str = "Insufficient stock"
    created_at: datetime = Field(default_factory=utcnow)


class WorkOrder(BaseModel):
    """A unit of service work against a generator."""

    id: str
    generator_id: str
    customer_id: str
    type: WorkOrderType
    status: WorkOrderStatus = WorkOrderStatus.CREATED
    priority: Priority = Priority.NORMAL
    assigned_technician_id: Optional[str] = None
    required_parts: List[RequiredPart] = Field(default_factory=list)
    reservation_ids: List[str] = Field(default_factory=list)
    purchase_request_ids: List[str] = Field(default_factory=list)
    scheduled_date: Optional[datetime] = None
    running_hours_recorded: Optional[float] = None
    faults: List[FaultRecord] = Field(default_factory=list)
    photo_urls: List[str] = Field(default_factory=list)
    customer_signature: Optional[str] = None
    labor_hours: float = 0.0
    incident_id: Optional[str] = None
    invoice_id: Optional[str] = None
    notes: str = ""
    created_at: datetime = Field(default_factory=utcnow)
    closed_at: Optional[datetime] = None


class Contract(BaseModel):
    """A service contract governing coverage and billability."""

    id: str
    customer_id: str
    type: ContractType
    covered_generator_ids: List[str] = Field(default_factory=list)
    start_date: date
    end_date: date
    covers_parts: bool = False
    covers_labor: bool = False

    def is_active_on(self, when: date) -> bool:
        """Whether the contract is in force on a given date."""
        return self.start_date <= when <= self.end_date


class Incident(BaseModel):
    """An emergency breakdown reported by a customer."""

    id: str
    customer_id: str
    generator_id: str
    description: str
    priority: Priority
    work_order_id: Optional[str] = None
    created_at: datetime = Field(default_factory=utcnow)


class InvoiceLine(BaseModel):
    """A single billable (or covered) line on an invoice."""

    description: str
    quantity: float
    unit_price: float
    amount: float
    covered: bool = False
    coverage_note: str = ""


class Invoice(BaseModel):
    """The invoice produced when a work order closes."""

    id: str
    work_order_id: str
    customer_id: str
    lines: List[InvoiceLine] = Field(default_factory=list)
    parts_total: float = 0.0
    labor_total: float = 0.0
    total: float = 0.0
    billable: bool = True
    contract_id: Optional[str] = None
    created_at: datetime = Field(default_factory=utcnow)


class MaintenanceRecommendation(BaseModel):
    """A predictive-maintenance recommendation from sensor analytics."""

    generator_id: str
    severity: Priority
    reason: str
    recommended_action: WorkOrderType


class SensorReading(BaseModel):
    """An IoT telemetry sample from a generator."""

    oil_pressure: Optional[float] = None  # bar
    coolant_temp: Optional[float] = None  # deg C
    battery_voltage: Optional[float] = None  # volts
    fuel_level: Optional[float] = None  # percent
    running_hours: Optional[float] = None
    frequency: Optional[float] = None  # Hz
    voltage: Optional[float] = None  # volts
    load_pct: Optional[float] = None  # percent


# ---------------------------------------------------------------------------
# Coverage result (returned by the contract manager)
# ---------------------------------------------------------------------------


class Coverage(BaseModel):
    """The result of a contract-coverage check for a piece of work."""

    contract_id: Optional[str] = None
    contract_type: Optional[ContractType] = None
    covers_parts: bool = False
    covers_labor: bool = False

    @property
    def is_covered(self) -> bool:
        return self.contract_id is not None
