"""Reading the user's question.

The chat box accepts two shapes: an open question ("Why did this patient
fail?") and a hypothesis ("Did the patient fail because of MTHFR?"). The second
shape is what makes the critic's job meaningful — a named hypothesis is
something evidence can support or contradict — so it is worth detecting
properly rather than treating every question as open-ended.
"""

from __future__ import annotations

import re

_HYPOTHESIS_PATTERNS = (
    re.compile(r"\bbecause of\s+(?P<h>.+?)\s*[?.!]*$", re.IGNORECASE),
    re.compile(r"\bdue to\s+(?P<h>.+?)\s*[?.!]*$", re.IGNORECASE),
    re.compile(r"\bcaused by\s+(?P<h>.+?)\s*[?.!]*$", re.IGNORECASE),
    re.compile(r"\bdriven by\s+(?P<h>.+?)\s*[?.!]*$", re.IGNORECASE),
    re.compile(r"^is (?:it|this) (?:the )?(?P<h>.+?)\s*[?.!]*$", re.IGNORECASE),
)

# Gene symbols are upper-case alphanumerics; the stop set keeps common clinical
# acronyms and question words from being read as genes.
_GENE_RE = re.compile(r"\b([A-Z][A-Z0-9]{2,7})\b")
_NOT_GENES = {
    "CEA", "ECOG", "CT", "MRI", "PET", "MDT", "DNA", "RNA", "USA", "NHS",
    "FOLFIRI", "FOLFOX", "PASS", "GT", "AND", "THE", "WHY", "DID", "HAS",
    "ALT", "AST", "LDH", "CRP", "WBC", "HGB", "PD", "SD", "PR", "CR",
    "CPIC", "FDA", "EMA", "NICE", "ESMO", "ASCO", "CT", "MDT",
}


def extract_hypothesis(question: str) -> str | None:
    """The thing the user is proposing as the cause, if they proposed one."""
    text = question.strip()
    for pattern in _HYPOTHESIS_PATTERNS:
        match = pattern.search(text)
        if match:
            hypothesis = match.group("h").strip().strip(",;")
            if hypothesis:
                return hypothesis
    return None


def mentioned_genes(text: str) -> list[str]:
    """Gene symbols named in free text, in order of first appearance."""
    seen: list[str] = []
    for token in _GENE_RE.findall(text or ""):
        if token in _NOT_GENES or token in seen:
            continue
        seen.append(token)
    return seen


def is_open_question(question: str) -> bool:
    return extract_hypothesis(question) is None
