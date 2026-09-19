"""The literature corpus subset, and the vector maths over it.

Used in both run modes: the documents are ours either way, and only the
embedder behind `BioProvider.embed` changes. Keeping retrieval here means the
literature agent's ranking code is exercised identically in mock and live runs.
"""

from __future__ import annotations

import json
import math
from functools import lru_cache
from pathlib import Path
from typing import Any

CORPUS_PATH = Path(__file__).resolve().parent.parent / "fixtures" / "corpus.json"


@lru_cache(maxsize=1)
def documents() -> list[dict[str, Any]]:
    data = json.loads(CORPUS_PATH.read_text(encoding="utf-8"))
    return list(data["documents"])


def document_text(doc: dict[str, Any]) -> str:
    return " ".join([doc.get("title", ""), doc.get("text", ""), " ".join(doc.get("tags", []))])


def cosine(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(y * y for y in b))
    if na == 0.0 or nb == 0.0:
        return 0.0
    return dot / (na * nb)
