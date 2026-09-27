"""End-to-end workflow tests over the HTTP API and the orchestrator."""

from __future__ import annotations

from app.models import WorkOrderStatus, WorkOrderType

# ---------------------------------------------------------------------------
# Emergency breakdown, end to end over the REST API
# ---------------------------------------------------------------------------


def test_emergency_breakdown_end_to_end(client):
    # 1. Report a breakdown on the hospital's warranty generator.
    resp = client.post(
        "/incidents",
        json={
            "generator_id": "GEN-000002",
            "description": "Generator failed to start on mains failure",
            "priority": "EMERGENCY",
            "required_parts": [{"category": "BATTERY", "quantity": 1}],
        },
    )
    assert resp.status_code == 201
    body = resp.json()

    # A work order was created, a technician dispatched, coverage resolved.
    wo = body["work_order"]
    assert wo["type"] == "BREAKDOWN"
    assert wo["priority"] == "EMERGENCY"
    assert body["technician"] is not None
    assert wo["assigned_technician_id"] == body["technician"]["id"]
    assert body["coverage"]["contract_id"] is not None  # AMC covers this gen
    assert len(body["reservations"]) == 1

    wo_id = wo["id"]

    # 2. Technician records running hours, logs a fault, fits the part.
    assert client.post(
        f"/work-orders/{wo_id}/running-hours", json={"hours": 215.0}
    ).status_code == 200
    assert client.post(
        f"/work-orders/{wo_id}/faults",
        json={"code": "E-041", "description": "Flat starter battery"},
    ).status_code == 200
    res_id = body["reservations"][0]["id"]
    assert client.post(
        f"/work-orders/{wo_id}/replace-part", json={"reservation_id": res_id}
    ).status_code == 200

    # 3. Capture signature and close -> invoice.
    assert client.post(
        f"/work-orders/{wo_id}/signature", json={"signature": "S. Cole"}
    ).status_code == 200
    close = client.post(
        f"/work-orders/{wo_id}/close",
        json={"labor_hours": 1.5, "summary": "Battery replaced"},
    )
    assert close.status_code == 200
    invoice = close.json()

    # AMC on GEN-000002 covers labor; battery (a part) is billable.
    assert invoice["labor_total"] == 0.0
    assert invoice["parts_total"] > 0.0
    assert invoice["billable"] is True

    # 4. Work order is closed and recorded in the generator's history.
    wo_after = client.get(f"/work-orders/{wo_id}").json()
    assert wo_after["status"] == WorkOrderStatus.CLOSED.value
    history = client.get("/generators/GEN-000002/history").json()
    assert any(h["work_order_id"] == wo_id for h in history)


# ---------------------------------------------------------------------------
# Preventive maintenance scheduling
# ---------------------------------------------------------------------------


def test_daily_scheduler_targets_only_due_generators(client):
    due = client.get("/maintenance/due").json()
    due_ids = {g["id"] for g in due}
    # Seeded generators GEN-000001/3/5 are past their PM interval; 2/4 are not.
    assert {"GEN-000001", "GEN-000003", "GEN-000005"}.issubset(due_ids)
    assert "GEN-000002" not in due_ids
    assert "GEN-000004" not in due_ids

    resp = client.post("/maintenance/run-daily")
    assert resp.status_code == 200
    results = resp.json()
    assert len(results) == len(due_ids)
    for r in results:
        assert r["work_order"]["type"] == WorkOrderType.PREVENTIVE.value

    # Running it again is idempotent while the PM work orders remain open.
    again = client.post("/maintenance/run-daily").json()
    assert again == []


def test_pm_close_resets_interval(orch, store):
    results = orch.schedule_preventive_maintenance()
    wo = next(
        r.work_order for r in results if r.work_order.generator_id == "GEN-000001"
    )
    generator = store.generators["GEN-000001"]
    orch.record_running_hours(wo.id, 1320.0)
    orch.close_work_order(wo.id, labor_hours=2.0)
    # last_pm_hours is bumped so the generator is no longer due.
    assert generator.last_pm_hours == 1320.0
    assert not orch.maintenance.is_due(generator)


# ---------------------------------------------------------------------------
# Predictive maintenance
# ---------------------------------------------------------------------------


def test_low_oil_pressure_recommends_oil_change(client):
    resp = client.post(
        "/generators/GEN-000004/readings",
        json={"oil_pressure": 0.9, "coolant_temp": 80, "battery_voltage": 12.6},
    )
    assert resp.status_code == 200
    recs = resp.json()
    actions = {r["recommended_action"] for r in recs}
    assert "OIL_CHANGE" in actions


# ---------------------------------------------------------------------------
# Reporting
# ---------------------------------------------------------------------------


def test_dashboard_reports_kpis(client):
    data = client.get("/reporting/dashboard").json()
    assert data["active_generators"] == 5
    assert data["generators_under_contract"] >= 3
    assert data["upcoming_preventive_maintenance"] == 3
    # Keys for the full KPI set are present.
    for key in (
        "mttr_hours",
        "first_time_fix_rate",
        "technician_utilization",
        "parts_consumption",
        "revenue_by_contract",
    ):
        assert key in data
