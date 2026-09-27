"""Error-path tests for the shared 404 handler.

Store lookup misses are raised as ``KeyError`` by the ``require_*`` helpers and
translated to a 404 by a single app-level exception handler (see
``app.main.create_app``). These tests pin that behavior across a few endpoints
so a route that forgets to guard an unknown id still fails cleanly.
"""

from __future__ import annotations

import pytest


@pytest.mark.parametrize(
    "method, path, json_body",
    [
        ("get", "/generators/GEN-DOES-NOT-EXIST", None),
        ("get", "/generators/GEN-DOES-NOT-EXIST/history", None),
        ("get", "/work-orders/WO-DOES-NOT-EXIST", None),
        ("get", "/contracts/coverage?generator_id=GEN-DOES-NOT-EXIST", None),
        (
            "post",
            "/incidents",
            {"generator_id": "GEN-DOES-NOT-EXIST", "description": "x"},
        ),
        (
            "post",
            "/work-orders/WO-DOES-NOT-EXIST/close",
            {"labor_hours": 1.0},
        ),
        (
            "post",
            "/dispatch/preview",
            {"generator_id": "GEN-DOES-NOT-EXIST"},
        ),
    ],
)
def test_unknown_id_returns_clean_404(client, method, path, json_body):
    kwargs = {"json": json_body} if json_body is not None else {}
    resp = getattr(client, method)(path, **kwargs)
    assert resp.status_code == 404
    detail = resp.json()["detail"]
    # The message is surfaced without the quotes that ``str(KeyError(...))`` adds.
    assert "DOES-NOT-EXIST" in detail
    assert not detail.startswith("'")


def test_register_generator_for_unknown_customer_is_404(client):
    resp = client.post(
        "/generators",
        json={
            "customer_id": "CUST-DOES-NOT-EXIST",
            "serial_number": "SN-1",
            "model": "M",
            "engine": "E",
            "alternator": "A",
            "controller": "C",
            "installation_date": "2024-01-01",
            "location": {"lat": 0.0, "lng": 0.0},
        },
    )
    assert resp.status_code == 404
    assert "CUST-DOES-NOT-EXIST" in resp.json()["detail"]
