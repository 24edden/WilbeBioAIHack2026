"""Expanded-study input validation, with no provider transport or inference."""
import asyncio

import pytest

from app import providers as p


class TransportConstructionReached(Exception):
    """Sentinel proving investigation input validation completed."""


@pytest.fixture
def transport_constructions(monkeypatch):
    calls = []

    def model_session(*args, **kwargs):
        calls.append((args, kwargs))
        raise TransportConstructionReached

    monkeypatch.setattr(p, "ModelSession", model_session)
    return calls


def evidence_packet(serialized_chars):
    # Two studies mirror the combined evidence packet that exceeded the old cap.
    evidence = [{"id": "original-study", "summary": "x" * 98_000},
                {"id": "additional-study", "summary": ""}]
    remaining = serialized_chars - len(p._json(evidence))
    assert remaining >= 0
    evidence[1]["summary"] = "y" * remaining
    assert len(p._json(evidence)) == serialized_chars
    return evidence


def investigate(evidence):
    async def emit(*args, **kwargs):
        pass

    return asyncio.run(p.investigate(
        {"id": "case-1"}, "The supplied hypothesis.", evidence, emit, lambda: False))


@pytest.mark.parametrize("serialized_chars", [156_695, 300_000])
def test_expanded_study_packet_reaches_transport_construction(
        serialized_chars, transport_constructions):
    assert serialized_chars > 150_000
    with pytest.raises(TransportConstructionReached):
        investigate(evidence_packet(serialized_chars))
    assert len(transport_constructions) == 1


def test_above_expanded_bound_is_rejected_before_transport(transport_constructions):
    assert p.EVIDENCE_MAX_INPUT_CHARS == 300_000
    with pytest.raises(p.ProviderError, match="bounded model input limit") as error:
        investigate(evidence_packet(300_001))
    assert error.value.status == "failed"
    assert transport_constructions == []


@pytest.mark.parametrize("invalid_id", ["original-study", ""])
def test_duplicate_or_empty_evidence_id_still_rejected_before_transport(
        invalid_id, transport_constructions):
    evidence = evidence_packet(156_695)
    evidence[1]["id"] = invalid_id
    with pytest.raises(p.ProviderError, match="unique, nonempty IDs"):
        investigate(evidence)
    assert transport_constructions == []
