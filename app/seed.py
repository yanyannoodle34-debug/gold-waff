"""Seed data for the in-memory store.

Builds a small but representative operating picture: several customers, a fleet of
generators (some due for PM, some under warranty), technicians with differing
skills and locations, a spare-parts inventory (a couple below reorder level to
exercise the purchase-request path), and a mix of contracts so billability varies.
"""

from __future__ import annotations

from datetime import date

from .models import (
    Contract,
    ContractType,
    Customer,
    Generator,
    GeoLocation,
    PartCategory,
    SparePart,
    Technician,
)
from .store import InMemoryStore


def seed_store(store: InMemoryStore) -> None:
    """Populate an empty store with representative sample data."""
    _seed_customers(store)
    _seed_generators(store)
    _seed_technicians(store)
    _seed_parts(store)
    _seed_contracts(store)
    store.log("[Seed] Sample data loaded")


def _seed_customers(store: InMemoryStore) -> None:
    customers = [
        Customer(
            id="CUS-000001",
            name="Meridian Data Centre",
            contact_name="Priya Nair",
            phone="+971-50-1112233",
            email="ops@meridian-dc.example",
            address="Dubai Silicon Oasis",
        ),
        Customer(
            id="CUS-000002",
            name="Harbour General Hospital",
            contact_name="Dr. Samuel Cole",
            phone="+971-50-4455667",
            email="facilities@harbourgh.example",
            address="Deira, Dubai",
        ),
        Customer(
            id="CUS-000003",
            name="Falcon Logistics Depot",
            contact_name="Omar Haddad",
            phone="+971-52-9988776",
            email="maintenance@falconlog.example",
            address="Jebel Ali Free Zone",
        ),
    ]
    for c in customers:
        store.customers[c.id] = c
    # Advance the counter past the seeded ids.
    for _ in customers:
        store.next_id("CUS")


def _seed_generators(store: InMemoryStore) -> None:
    generators = [
        # Due for PM (running_hours - last_pm_hours >= interval).
        Generator(
            id="GEN-000001",
            customer_id="CUS-000001",
            serial_number="CAT-DE-88213",
            model="Caterpillar DE1100",
            engine="Cat C32 Diesel",
            alternator="Cat LC6114",
            controller="EMCP 4.4",
            installation_date=date(2021, 3, 12),
            running_hours=1320.0,
            last_pm_hours=1050.0,
            pm_interval_hours=250.0,
            location=GeoLocation(lat=25.118, lng=55.377, label="Silicon Oasis"),
            warranty_until=date(2024, 3, 12),
        ),
        # Under warranty, not yet due.
        Generator(
            id="GEN-000002",
            customer_id="CUS-000002",
            serial_number="CUM-DG-40567",
            model="Cummins C900D5",
            engine="Cummins QSK23",
            alternator="Stamford HCI634",
            controller="PowerCommand 3.3",
            installation_date=date(2024, 1, 20),
            running_hours=210.0,
            last_pm_hours=0.0,
            pm_interval_hours=250.0,
            location=GeoLocation(lat=25.271, lng=55.307, label="Deira"),
            warranty_until=date(2027, 1, 20),
        ),
        # Due for PM.
        Generator(
            id="GEN-000003",
            customer_id="CUS-000002",
            serial_number="CUM-DG-40892",
            model="Cummins C700D5",
            engine="Cummins QSX15",
            alternator="Stamford HCI544",
            controller="PowerCommand 2.3",
            installation_date=date(2020, 8, 5),
            running_hours=3120.0,
            last_pm_hours=2800.0,
            pm_interval_hours=300.0,
            location=GeoLocation(lat=25.269, lng=55.309, label="Deira Annex"),
            warranty_until=date(2023, 8, 5),
        ),
        # Not due.
        Generator(
            id="GEN-000004",
            customer_id="CUS-000003",
            serial_number="PRK-DG-11204",
            model="Perkins P1000E",
            engine="Perkins 4012-46TWG",
            alternator="Leroy Somer LSA 50.2",
            controller="DSE 8610",
            installation_date=date(2022, 11, 2),
            running_hours=640.0,
            last_pm_hours=500.0,
            pm_interval_hours=250.0,
            location=GeoLocation(lat=24.985, lng=55.061, label="Jebel Ali"),
            warranty_until=date(2025, 11, 2),
        ),
        # Due for PM.
        Generator(
            id="GEN-000005",
            customer_id="CUS-000003",
            serial_number="PRK-DG-11533",
            model="Perkins P1250E",
            engine="Perkins 4012-46TWG2A",
            alternator="Leroy Somer LSA 52.3",
            controller="DSE 8620",
            installation_date=date(2019, 6, 18),
            running_hours=5400.0,
            last_pm_hours=5100.0,
            pm_interval_hours=250.0,
            location=GeoLocation(lat=24.990, lng=55.055, label="Jebel Ali South"),
            warranty_until=date(2022, 6, 18),
        ),
    ]
    for g in generators:
        store.generators[g.id] = g
    for _ in generators:
        store.next_id("GEN")


def _seed_technicians(store: InMemoryStore) -> None:
    technicians = [
        Technician(
            id="TEC-000001",
            name="Rashid Al-Amiri",
            skills=["mechanical", "electrical", "engine", "load_testing"],
            certifications=["Caterpillar Certified", "HV Electrical"],
            location=GeoLocation(lat=25.120, lng=55.370, label="Silicon Oasis"),
            is_available=True,
            current_workload=1,
            max_workload=5,
        ),
        Technician(
            id="TEC-000002",
            name="Grace Mensah",
            skills=["mechanical", "electrical"],
            certifications=["Cummins Certified"],
            location=GeoLocation(lat=25.260, lng=55.310, label="Deira"),
            is_available=True,
            current_workload=0,
            max_workload=4,
        ),
        Technician(
            id="TEC-000003",
            name="Vikram Shetty",
            skills=["mechanical"],
            certifications=["Perkins Certified"],
            location=GeoLocation(lat=24.980, lng=55.060, label="Jebel Ali"),
            is_available=True,
            current_workload=2,
            max_workload=5,
        ),
        Technician(
            id="TEC-000004",
            name="Lena Fischer",
            skills=["mechanical", "electrical", "engine", "load_testing"],
            certifications=["Caterpillar Certified", "Cummins Certified"],
            location=GeoLocation(lat=25.200, lng=55.270, label="Business Bay"),
            is_available=True,
            current_workload=3,
            max_workload=5,
        ),
    ]
    for t in technicians:
        store.technicians[t.id] = t
    for _ in technicians:
        store.next_id("TEC")


def _seed_parts(store: InMemoryStore) -> None:
    # (name, category, on_hand, reorder_level, unit_price)
    parts = [
        ("15W-40 Engine Oil (20L)", PartCategory.ENGINE_OIL, 40, 10, 95.0),
        ("Fuel Filter FF-500", PartCategory.FUEL_FILTER, 25, 8, 42.0),
        ("Oil Filter OF-220", PartCategory.OIL_FILTER, 30, 8, 28.5),
        ("Air Filter AF-880", PartCategory.AIR_FILTER, 18, 6, 55.0),
        ("Drive Belt DB-14", PartCategory.BELT, 12, 5, 33.0),
        # Below reorder level -> exercises purchase-request path when demanded.
        ("Starter Battery 12V 200Ah", PartCategory.BATTERY, 2, 4, 320.0),
        ("AVR SX440", PartCategory.AVR, 3, 2, 480.0),
        ("Controller EMCP 4.4", PartCategory.CONTROLLER, 1, 2, 1650.0),
        ("Coolant Temp Sensor", PartCategory.SENSOR, 15, 5, 60.0),
        ("Fuel Injector INJ-90", PartCategory.INJECTOR, 6, 4, 210.0),
    ]
    for name, category, on_hand, reorder, price in parts:
        part = SparePart(
            id=store.next_id("SP"),
            name=name,
            category=category,
            on_hand=on_hand,
            reserved=0,
            reorder_level=reorder,
            unit_price=price,
        )
        store.parts[part.id] = part


def _seed_contracts(store: InMemoryStore) -> None:
    contracts = [
        # CMC: parts + labor covered for Meridian's generator.
        Contract(
            id="CON-000001",
            customer_id="CUS-000001",
            type=ContractType.CMC,
            covered_generator_ids=["GEN-000001"],
            start_date=date(2026, 1, 1),
            end_date=date(2026, 12, 31),
            covers_parts=True,
            covers_labor=True,
        ),
        # AMC: labor covered, parts billable for the hospital's fleet.
        Contract(
            id="CON-000002",
            customer_id="CUS-000002",
            type=ContractType.AMC,
            covered_generator_ids=["GEN-000002", "GEN-000003"],
            start_date=date(2026, 1, 1),
            end_date=date(2026, 12, 31),
            covers_parts=False,
            covers_labor=True,
        ),
        # Falcon GEN-000004 has no contract (fully billable). GEN-000005 covered
        # by an emergency-support contract (response only, nothing covered).
        Contract(
            id="CON-000003",
            customer_id="CUS-000003",
            type=ContractType.EMERGENCY_SUPPORT,
            covered_generator_ids=["GEN-000005"],
            start_date=date(2026, 1, 1),
            end_date=date(2026, 12, 31),
            covers_parts=False,
            covers_labor=False,
        ),
    ]
    for c in contracts:
        store.contracts[c.id] = c
    for _ in contracts:
        store.next_id("CON")
