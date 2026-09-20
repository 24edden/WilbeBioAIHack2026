"""Explicit legacy policy for tests of pre-governance manual workflows."""
from app.store import digest


def pin_legacy_manual_policy(store, run_id):
    def update(run):
        contract = run["process_contract"]
        contract.pop("hypothesis_governance", None)
        contract["version"] = "test-legacy-manual-policy"
        contract.pop("sha256", None)
        contract["sha256"] = digest(contract)
    return store.mutate(run_id, update)
