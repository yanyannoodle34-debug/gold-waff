"""Contract manager: coverage resolution across contract types."""

from __future__ import annotations

from app.models import ContractType


def test_cmc_covers_parts_and_labor(orch):
    cov = orch.contracts.coverage("CUS-000001", "GEN-000001")
    assert cov.is_covered
    assert cov.contract_type == ContractType.CMC
    assert cov.covers_parts and cov.covers_labor


def test_amc_covers_labor_only(orch):
    cov = orch.contracts.coverage("CUS-000002", "GEN-000003")
    assert cov.is_covered
    assert cov.contract_type == ContractType.AMC
    assert cov.covers_labor and not cov.covers_parts


def test_emergency_support_covers_nothing(orch):
    cov = orch.contracts.coverage("CUS-000003", "GEN-000005")
    assert cov.is_covered
    assert cov.contract_type == ContractType.EMERGENCY_SUPPORT
    assert not cov.covers_parts and not cov.covers_labor


def test_uncovered_generator_is_billable(orch):
    # GEN-000004 has no contract at all.
    cov = orch.contracts.coverage("CUS-000003", "GEN-000004")
    assert not cov.is_covered
