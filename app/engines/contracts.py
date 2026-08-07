"""Contract manager.

Determines whether a piece of work on a generator is covered by an active
contract, and how (parts and/or labor). The orchestrator consults this before
approving work; the billing engine consults it to decide what is billable.
"""

from __future__ import annotations

from datetime import date

from ..models import Contract, ContractType, Coverage
from ..store import InMemoryStore


class ContractManager:
    def __init__(self, store: InMemoryStore) -> None:
        self.store = store

    def coverage(
        self, customer_id: str, generator_id: str, when: date | None = None
    ) -> Coverage:
        """Return the best coverage for work on a generator on a given date.

        Contracts are ranked by how much they cover (parts + labor beats labor
        only), so the customer always gets the most favorable active contract.
        A WARRANTY contract only applies while the generator is within its
        warranty window.
        """
        when = when or date.today()
        best: Coverage = Coverage()
        best_score = -1

        for contract in self.store.contracts_for_customer(customer_id):
            if generator_id not in contract.covered_generator_ids:
                continue
            if not contract.is_active_on(when):
                continue
            if not self._applies(contract, generator_id, when):
                continue

            score = int(contract.covers_parts) + int(contract.covers_labor)
            if score > best_score:
                best_score = score
                best = Coverage(
                    contract_id=contract.id,
                    contract_type=contract.type,
                    covers_parts=contract.covers_parts,
                    covers_labor=contract.covers_labor,
                )

        return best

    def _applies(self, contract: Contract, generator_id: str, when: date) -> bool:
        """Extra per-type applicability rules beyond the active-date window."""
        if contract.type == ContractType.WARRANTY:
            generator = self.store.generators.get(generator_id)
            if generator is None or generator.warranty_until is None:
                return False
            return when <= generator.warranty_until
        return True
