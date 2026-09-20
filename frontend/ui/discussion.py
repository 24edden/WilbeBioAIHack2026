"""Inspect recorded reply links without inferring an argument from its position."""
from collections import defaultdict
from dataclasses import dataclass


@dataclass(frozen=True)
class ReplyInspection:
    status: str
    message: str = ""
    target_index: int | None = None
    chain: tuple[int, ...] = ()


def inspect_replies(entries: list[dict]) -> list[ReplyInspection]:
    """Resolve exact, unique IDs and reject invalid chains before showing a link.

    Indices refer to the original record order. A valid parent must precede its
    reply. Traverse before checking that ordering so a cycle has an explicit
    explanation rather than masquerading as an ordinary later reference.
    """
    by_id = defaultdict(list)
    for index, entry in enumerate(entries):
        identifier = entry.get("id")
        if isinstance(identifier, str) and identifier.strip():
            by_id[identifier].append(index)

    def inspect(start):
        identifier = entries[start].get("id")
        if not isinstance(identifier, str) or not identifier.strip():
            return ReplyInspection("legacy", "This turn has no usable identifier. Its reply link cannot be verified.")
        if len(by_id[identifier]) != 1:
            return ReplyInspection("ambiguous", "This turn's identifier is duplicated. Its reply link is ambiguous.")
        if entries[start].get("reply_to") in (None, ""):
            return ReplyInspection("unlinked", "No earlier argument was linked to this turn.")

        chain, seen, current, out_of_order = [], set(), start, False
        while True:
            chain.append(current)
            seen.add(current)
            reply_to = entries[current].get("reply_to")
            if reply_to in (None, ""):
                break
            if not isinstance(reply_to, str) or not reply_to.strip():
                return ReplyInspection("invalid", "The recorded reply identifier is not a usable text ID. No argument was substituted.")
            matches = by_id.get(reply_to, [])
            if not matches:
                return ReplyInspection("missing", "A referenced argument is missing from this record. No argument was substituted.")
            if len(matches) != 1:
                return ReplyInspection("ambiguous", "A referenced identifier matches multiple turns. No argument was selected.")
            target = matches[0]
            if target == current:
                return ReplyInspection("self", "A turn links to itself. The reply chain cannot be shown.")
            if target in seen:
                return ReplyInspection("cycle", "The recorded reply links contain a cycle. The reply chain cannot be shown.")
            out_of_order = out_of_order or target > current
            current = target
        if out_of_order:
            return ReplyInspection("out_of_order", "A reply points to a later turn. It cannot be shown as an earlier argument.")
        return ReplyInspection("linked", target_index=chain[1], chain=tuple(reversed(chain)))

    return [inspect(index) for index in range(len(entries))]
