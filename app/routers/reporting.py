"""Reporting dashboard."""

from __future__ import annotations

from typing import List

from fastapi import APIRouter

from ..reporting import build_dashboard
from ..store import get_store

router = APIRouter(prefix="/reporting", tags=["Reporting"])


@router.get("/dashboard")
def dashboard() -> dict:
    """The full KPI dashboard for the service operation."""
    return build_dashboard(get_store())


@router.get("/logs", response_model=List[str])
def logs(limit: int = 100) -> List[str]:
    """Recent orchestration log lines (customer notifications, dispatch, etc.)."""
    return get_store().logs[-limit:]
