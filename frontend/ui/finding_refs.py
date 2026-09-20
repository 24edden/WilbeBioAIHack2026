"""Exact local finding lookup and bounded preparation of attached source records."""
from collections import defaultdict
from dataclasses import dataclass
from typing import Any

from .state import Finding


@dataclass(frozen=True)
class FindingReference:
    identifier: Any
    status: str
    finding: Finding | None = None
    message: str = ""


class FindingReferenceIndex:
    def __init__(self, findings: list[Finding]):
        self.by_id = defaultdict(list)
        self.legacy_count = 0
        for finding in findings:
            identifier = getattr(finding, "finding_id", None)
            if isinstance(identifier, str) and identifier.strip():
                self.by_id[identifier].append(finding)
            else:
                self.legacy_count += 1

    def resolve(self, identifier: Any) -> FindingReference:
        if not isinstance(identifier, str) or not identifier.strip():
            return FindingReference(identifier, "invalid", message="The reference is not a usable finding ID. No finding was substituted.")
        matches = self.by_id.get(identifier, [])
        if len(matches) == 1:
            return FindingReference(identifier, "matched", finding=matches[0])
        if len(matches) > 1:
            return FindingReference(identifier, "ambiguous", message="Multiple findings share this ID. No finding was selected.")
        legacy_note = (f" {self.legacy_count} finding(s) in this record lack IDs and cannot be matched."
                       if self.legacy_count else "")
        return FindingReference(identifier, "missing", message="No exact finding ID matches this reference." + legacy_note)


def compact_provenance(value: Any, *, character_budget: int = 12000, node_budget: int = 192) -> bool:
    """Inspect only a bounded amount of metadata before deciding to defer it.

    No serialization is needed to decide. Stop immediately on a large string,
    collection or deeply structured record rather than copying it into the UI.
    """
    pending = [value]
    while pending:
        if node_budget <= 0:
            return False
        node_budget -= 1
        item = pending.pop()
        if isinstance(item, str):
            character_budget -= len(item)
            if character_budget < 0:
                return False
        elif isinstance(item, dict):
            if 2 * len(item) > node_budget:
                return False
            pending.extend(item.keys())
            pending.extend(item.values())
        elif isinstance(item, (list, tuple)):
            if len(item) > node_budget:
                return False
            pending.extend(item)
        elif item is not None and not isinstance(item, (bool, int, float)):
            return False
    return True
