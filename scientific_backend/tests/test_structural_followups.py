"""Synthetic provider responses establish software contracts, never biology."""
import asyncio
import json
import httpx
import pytest
from Bio.SeqUtils import seq3
from app import structural_followups as s
from app.providers import ProviderError


def mock_client(monkeypatch, handler):
    original = httpx.AsyncClient
    class Client(original):
        def __init__(self, **kwargs):
            super().__init__(**kwargs, transport=httpx.MockTransport(handler))
    monkeypatch.setattr(httpx, "AsyncClient", Client)
    monkeypatch.setenv("NVIDIA_API_KEY", "synthetic-test-secret")
    monkeypatch.delenv("BOLTZ2_NIM_URL", raising=False)


def synthetic_cif(sequence):
    from test_structure_preview import cif
    header = cif().decode().split("ATOM 1")[0]
    mapping = list(range(272)) if len(sequence) == 272 else list(range(10)) + list(range(99, 272))
    rows = []
    for i, (amino, position) in enumerate(zip(sequence, mapping), 1):
        rows.append(f"ATOM {i} C CA . {seq3(amino).upper()} A 1 {i} ? {position}.0 {position % 7}.0 {position % 11}.0 1.0 60.0 1")
    return header + "\n".join(rows) + "\n#\n"


def test_exact_public_mapping_is_recomputed():
    inputs = s.qualified_inputs()
    assert (len(inputs["wild_type"]), len(inputs["exon2_deleted"])) == (272, 183)
    assert inputs["exon2_deleted"] == inputs["wild_type"][:10] + inputs["wild_type"][99:]
    assert inputs["mapping"]["matched_translation_residues"] == 186


def test_pending_provider_job_is_not_repeated(monkeypatch, tmp_path):
    calls = []
    def handler(request):
        calls.append(request)
        return httpx.Response(202, headers={"nvcf-reqid": "pending-fixture"}, json={"status": "pending"})
    mock_client(monkeypatch, handler)
    result = asyncio.run(s.execute(s.RECIPE, output_dir=tmp_path / "action"))
    assert result["status"] == "pending" and "evidence" not in result
    with pytest.raises(ProviderError, match="instead of resubmitting"):
        asyncio.run(s.execute(s.RECIPE, output_dir=tmp_path / "action"))
    assert len(calls) == 1


def test_completed_pair_preserves_scope_and_independently_validates_artifacts(monkeypatch, tmp_path):
    calls = []
    def handler(request):
        payload = json.loads(request.content)
        calls.append(payload)
        sequence = payload["polymers"][0]["sequence"]
        return httpx.Response(200, headers={"nvcf-reqid": "fixture-" + str(len(calls))}, json={
            "structures": [{"format": "mmcif", "structure": synthetic_cif(sequence)}], "confidence_scores": [.7]})
    mock_client(monkeypatch, handler)
    result = asyncio.run(s.execute(s.RECIPE, output_dir=tmp_path / "action"))
    assert result["status"] == "completed" and len(calls) == 2
    # A serialized/reloaded result must retain source and coordinate identity.
    evidence = json.loads(json.dumps(result["evidence"]))
    assert s.validate_evidence(evidence)
    assert evidence["values"]["binding_tested"] is False
    assert evidence["values"]["comparison"]["aligned_shared_backbone_rmsd_angstrom"] < 1e-8
    assert len(result["artifacts"]) == 2
    evidence["values"]["predictions"][1]["sequence_sha256"] = "0" * 64
    evidence["source"]["sha256"] = s._hash(evidence["values"])
    with pytest.raises(ValueError, match="Unverified"):
        s.validate_evidence(evidence)


def test_wrong_returned_sequence_does_not_publish_prediction(monkeypatch, tmp_path):
    def handler(request):
        sequence = json.loads(request.content)["polymers"][0]["sequence"]
        return httpx.Response(200, json={"structures": [{"format": "mmcif", "structure": synthetic_cif("A" + sequence[1:])}], "confidence_scores": [.7]})
    mock_client(monkeypatch, handler)
    result = asyncio.run(s.execute(s.RECIPE, output_dir=tmp_path / "action"))
    assert result["status"] == "failed" and "evidence" not in result
    assert result["artifacts"] == [] and len(result["jobs"]) == 1


def test_local_wait_timeout_preserves_unknown_and_blocks_resubmission(monkeypatch, tmp_path):
    from app import providers
    mock_client(monkeypatch, lambda request: httpx.Response(200, json={}))
    async def timeout(coro, *args):
        coro.close()
        raise TimeoutError("Synthetic interrupted provider wait")
    monkeypatch.setattr(providers, "_bounded", timeout)
    result = asyncio.run(s.execute(s.RECIPE, output_dir=tmp_path / "action"))
    assert result["status"] == "unknown" and "evidence" not in result
    saved = json.loads((tmp_path / "action" / "comparison.json").read_text())
    assert saved["jobs"][0]["status"] == "unknown"
