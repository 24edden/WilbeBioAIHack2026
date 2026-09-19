"""Fixture loading and the mock embedder.

The embedder is a hashing bag-of-words vectoriser rather than random noise, so
cosine similarity over the mock corpus returns genuinely relevant documents.
That matters: the literature agent's retrieval code is then exercised for real
in mock mode and only the embedding weights change when we switch to a NIM.
"""

from __future__ import annotations

import hashlib
import json
import math
import re
from functools import lru_cache
from pathlib import Path
from typing import Any

FIXTURE_DIR = Path(__file__).resolve().parents[2] / "fixtures"
EMBED_DIM = 256
_TOKEN_RE = re.compile(r"[a-z0-9][a-z0-9.\-+*>]*")


@lru_cache(maxsize=None)
def load(name: str) -> dict[str, Any]:
    path = FIXTURE_DIR / name
    if not path.exists():
        raise FileNotFoundError(f"fixture {name} not found in {FIXTURE_DIR}")
    return json.loads(path.read_text(encoding="utf-8"))


def variants_fixture() -> dict[str, Any]:
    return load("variants.json")


def corpus_documents() -> list[dict[str, Any]]:
    return list(load("corpus.json")["documents"])


def tokenize(text: str) -> list[str]:
    return _TOKEN_RE.findall(text.lower())


def hash_embed(text: str, dim: int = EMBED_DIM) -> list[float]:
    """Deterministic hashing vectoriser with L2 normalisation."""
    vector = [0.0] * dim
    for token in tokenize(text):
        digest = hashlib.blake2b(token.encode("utf-8"), digest_size=8).digest()
        index = int.from_bytes(digest[:4], "big") % dim
        sign = 1.0 if digest[4] % 2 == 0 else -1.0
        vector[index] += sign
    norm = math.sqrt(sum(v * v for v in vector))
    if norm == 0.0:
        return vector
    return [v / norm for v in vector]


def cosine(a: list[float], b: list[float]) -> float:
    return sum(x * y for x, y in zip(a, b))


def stable_unit(*parts: str) -> float:
    """A stable pseudo-random float in [0,1) from the given strings. Used for
    fallback scores and latency jitter so every run of a given input looks the
    same — a demo that reshuffles itself between rehearsals is a liability."""
    digest = hashlib.blake2b("|".join(parts).encode("utf-8"), digest_size=8).digest()
    return int.from_bytes(digest, "big") / 2**64
