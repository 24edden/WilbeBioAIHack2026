"""Public-source boundaries with fake subprocesses; no external requests."""
import asyncio
import copy
import json
import sys
from pathlib import Path

import pytest

from app import sequence_sources as s

SEQ = "ACDEFGHIKLMNPQRSTVWYA"


def entry(pdb_id="1ABC", ids=None):
    return {"rcsb_id": pdb_id, "struct": {"title": "Target complex with deposited research binders"},
        "rcsb_entry_container_identifiers": {"polymer_entity_ids": ids or ["1", "2", "3", "4"]},
        "rcsb_primary_citation": {"title": "Offline test publication"}}


def polymer(identifier, description, *, accession=None, seq=SEQ, kind="polypeptide(L)"):
    return {"rcsb_id": "1ABC_" + identifier,
        "entity_poly": {"pdbx_seq_one_letter_code_can": seq, "type": kind},
        "rcsb_polymer_entity": {"pdbx_description": description},
        "rcsb_polymer_entity_container_identifiers": {"entry_id": "1ABC", "entity_id": identifier, "auth_asym_ids": [identifier],
            "reference_sequence_identifiers": [{"database_name": "UniProt", "database_accession": accession}] if accession else []}}


def fake_processes(monkeypatch, tmp_path, *, data=None, raw=None, status=200, failure=None, missing_raw=False, output=None):
    calls = []
    root = tmp_path / "private-plugin"
    monkeypatch.setattr(s, "verify_life_sciences_runtime", lambda: root)
    class Process:
        returncode = None
        killed = False
        async def communicate(self, body):
            payload = json.loads(body)
            calls[-1]["payload"] = payload
            if not missing_raw:
                Path(payload["raw_output_path"]).write_bytes(raw if raw is not None else json.dumps(data if data is not None else {"results": []}).encode())
            self.returncode = 1 if failure else 0
            envelope = {"ok": not bool(failure), "status_code": status,
                        "sources": [{"url": payload["base_url"] + "/" + payload["path"]}], "checked_sources": []}
            if failure:
                envelope["error"] = {"code": failure}
            return (output if output is not None else json.dumps(envelope).encode()), b"private stderr must not be exported"
        def kill(self): self.killed = True
        async def wait(self): self.returncode = -9; return -9
    async def create(*args, **kwargs):
        calls.append({"args": args, "kwargs": kwargs})
        return Process()
    monkeypatch.setattr(s.asyncio, "create_subprocess_exec", create)
    return calls, root


def adapter(tmp_path):
    return s.SequenceSources(artifact_dir=tmp_path / "source-artifacts")


def test_exact_bytes_are_source_hashed_and_repeat_lookup_uses_cache(monkeypatch, tmp_path):
    raw = b'{ "results" : [] }\n'
    calls, root = fake_processes(monkeypatch, tmp_path, raw=raw)
    client = adapter(tmp_path)
    async def run():
        first = await client.search_uniprot("target name")
        second = await client.search_uniprot("target name")
        return first, second
    first, second = asyncio.run(run())
    assert first == second and len(calls) == 1 and len(client.receipts) == 1
    assert client.receipts[0]["source_sha256"] == s._hash(raw)
    assert client.receipts[0]["http_status"] == 200
    assert calls[0]["args"] == (sys.executable, str(root / "skills/uniprot-skill/scripts/rest_request.py"))
    assert client.sources == []  # Search results never become verified inputs.
    assert "private stderr" not in json.dumps(client.receipts)


def test_script_environment_excludes_keys_proxy_and_python_injection(monkeypatch, tmp_path):
    for name in ("OPENAI_API_KEY", "NVIDIA_API_KEY", "NGC_API_KEY", "AWS_SECRET_ACCESS_KEY", "HTTPS_PROXY", "PYTHONPATH", "HOME"):
        monkeypatch.setenv(name, "private-do-not-forward")
    monkeypatch.setenv("LANG", "en_US.UTF-8")
    calls, root = fake_processes(monkeypatch, tmp_path)
    asyncio.run(adapter(tmp_path).search_uniprot("target name"))
    environment = calls[0]["kwargs"]["env"]
    assert set(environment) <= {"PATH", "SYSTEMROOT", "SSL_CERT_FILE", "SSL_CERT_DIR", "LANG"}
    assert "private-do-not-forward" not in json.dumps(environment)
    assert calls[0]["payload"]["timeout_sec"] == 25
    assert calls[0]["payload"]["save_raw"] is True


@pytest.mark.parametrize("args,kwargs", [
    (("uniprot-skill", "https://evil.test", "uniprotkb/search"), {}),
    (("rcsb-pdb-skill", "https://data.rcsb.org/rest/v1", "../secrets"), {}),
    (("other-skill", "https://rest.uniprot.org", "uniprotkb/search"), {}),
    (("uniprot-skill", "https://rest.uniprot.org", "uniprotkb/search"), {"raw_output_path": "/tmp/untrusted"}),
    (("uniprot-skill", "https://rest.uniprot.org", "uniprotkb/search"), {"headers": {"Authorization": "forbidden"}}),
    (("uniprot-skill", "https://rest.uniprot.org", "uniprotkb/search"), {"response_format": "text"}),
])
def test_internal_source_routes_cannot_expand_authority(monkeypatch, tmp_path, args, kwargs):
    monkeypatch.setattr(s, "verify_life_sciences_runtime", lambda: pytest.fail("Rejected route must not open the runtime"))
    with pytest.raises(ValueError):
        asyncio.run(adapter(tmp_path)._request(*args, **kwargs))


@pytest.mark.parametrize("query", ["x", "a" * 161, "https://evil.test", "HTTPS://evil.test", "line\nbreak", "bad\x7fquery", "user@example.org"])
def test_invalid_public_queries_reject_before_script(monkeypatch, tmp_path, query):
    monkeypatch.setattr(s, "verify_life_sciences_runtime", lambda: pytest.fail("Invalid query cannot reach script"))
    with pytest.raises(ValueError):
        asyncio.run(adapter(tmp_path).search_uniprot(query))


def test_empty_rcsb_search_is_a_receipted_empty_result(monkeypatch, tmp_path):
    calls, _ = fake_processes(monkeypatch, tmp_path, raw=b"", status=204)
    client = adapter(tmp_path)
    result = asyncio.run(client.search_structures("no matching target"))
    assert result["records"] == [] and result["total_count"] == 0
    assert calls[0]["payload"]["response_format"] == "text"
    assert client.receipts[0]["http_status"] == 204
    assert client.receipts[0]["source_sha256"] == s._hash(b"")
    assert client.sources == []


@pytest.mark.parametrize("kwargs,error", [
    ({"failure": "network_error"}, "lookup failed"),
    ({"missing_raw": True}, "record-size"),
    ({"raw": b"not json"}, None),
    ({"data": []}, "object record"),
    ({"output": b"x" * 2_000_001}, "compact-output"),
])
def test_source_errors_are_recorded_without_accepting_inputs(monkeypatch, tmp_path, kwargs, error):
    fake_processes(monkeypatch, tmp_path, **kwargs)
    client = adapter(tmp_path)
    with pytest.raises((ValueError, json.JSONDecodeError), match=error):
        asyncio.run(client.search_uniprot("target name"))
    assert client.receipts[0]["status"] == "failed"
    assert client.sources == []


def test_lookup_limit_and_cancellation_prevent_subprocess(monkeypatch, tmp_path):
    monkeypatch.setattr(s, "verify_life_sciences_runtime", lambda: pytest.fail("Must not open runtime"))
    client = adapter(tmp_path)
    client._calls = 100
    with pytest.raises(ValueError, match="lookup bound"):
        asyncio.run(client.search_uniprot("target name"))
    client = s.SequenceSources(cancelled=lambda: True, artifact_dir=tmp_path)
    with pytest.raises(asyncio.CancelledError):
        asyncio.run(client.search_uniprot("target name"))


def test_script_start_failure_closes_its_public_source_receipt(monkeypatch, tmp_path):
    monkeypatch.setattr(s, "verify_life_sciences_runtime", lambda: tmp_path)
    async def fail(*args, **kwargs):
        raise OSError("Cannot start fixture")
    monkeypatch.setattr(s.asyncio, "create_subprocess_exec", fail)
    client = adapter(tmp_path)
    with pytest.raises(OSError):
        asyncio.run(client.search_uniprot("target name"))
    assert client.receipts[0]["status"] == "failed"
    assert client.receipts[0]["finished_at"]


def test_uniprot_identity_and_exact_sequence_record(monkeypatch, tmp_path):
    data = {"primaryAccession": "P00001", "sequence": {"value": SEQ}, "entryAudit": {"sequenceVersion": 4}}
    fake_processes(monkeypatch, tmp_path, data=data)
    client = adapter(tmp_path)
    value = asyncio.run(client.fetch_uniprot("P00001"))
    assert value["verified"] is True and value["sequence"] == SEQ
    assert value["sequence_sha256"] == s._hash(SEQ.encode())
    assert value["target_accessions"] == ["P00001"]
    assert value["provenance"]["entry_audit"]["sequenceVersion"] == 4
    fake_processes(monkeypatch, tmp_path, data={**data, "primaryAccession": "Q00001"})
    with pytest.raises(ValueError, match="accession does not match"):
        asyncio.run(adapter(tmp_path).fetch_uniprot("P00001"))


def structure_adapter(monkeypatch, tmp_path, *, changes=None):
    dataset = {"core/entry/1ABC": entry(),
        "core/polymer_entity/1ABC/1": polymer("1", "Target protein", accession="P00001"),
        "core/polymer_entity/1ABC/2": polymer("2", "Reference single-chain variable fragment", seq=SEQ + "C"),
        "core/polymer_entity/1ABC/3": polymer("3", "Alternative Fab heavy chain", seq=SEQ + "D"),
        "core/polymer_entity/1ABC/4": polymer("4", "Alternative Fab light chain", seq=SEQ + "E")}
    if changes:
        changes(dataset)
    client = adapter(tmp_path)
    async def request(skill, base, path, **kwargs):
        return copy.deepcopy(dataset[path]), {"id": path, "source_sha256": "a" * 64, "finished_at": "2026-09-20"}
    monkeypatch.setattr(client, "_request", request)
    return client


def test_complete_single_chain_and_isolated_fab_roles_remain_distinct(monkeypatch, tmp_path):
    client = structure_adapter(monkeypatch, tmp_path)
    result = asyncio.run(client.fetch_structure("1abc"))
    values = result["sequences"]
    assert [x["entity_type"] for x in values] == ["protein", "single_chain_binder", "antibody_chain", "antibody_chain"]
    assert [x["sequence"] for x in values] == [SEQ, SEQ + "C", SEQ + "D", SEQ + "E"]
    assert all(x["target_accessions"] == ["P00001"] for x in values)
    assert len(client.sources) == 4
    assert "Co-deposition" in result["note"]
    asyncio.run(client.fetch_structure("1ABC"))
    assert len(client.sources) == 4


@pytest.mark.parametrize("change,error", [
    (lambda d: d["core/entry/1ABC"].update(rcsb_id="2XYZ"), "entry identity"),
    (lambda d: d["core/polymer_entity/1ABC/2"].update(rcsb_id="1ABC_7"), "polymer identity"),
    (lambda d: d["core/polymer_entity/1ABC/2"]["rcsb_polymer_entity_container_identifiers"].update(entry_id="2XYZ"), "polymer identity"),
    (lambda d: d["core/polymer_entity/1ABC/2"]["rcsb_polymer_entity_container_identifiers"].update(entity_id="7"), "polymer identity"),
])
def test_wrong_entry_or_entity_cannot_be_labeled_as_requested(monkeypatch, tmp_path, change, error):
    client = structure_adapter(monkeypatch, tmp_path, changes=change)
    with pytest.raises(ValueError, match=error):
        asyncio.run(client.fetch_structure("1ABC"))
    assert client.sources == []


def test_nonprotein_and_unresolved_sequences_are_not_verified(monkeypatch, tmp_path):
    def change(data):
        data["core/polymer_entity/1ABC/1"]["entity_poly"].update(type="polydeoxyribonucleotide", pdbx_seq_one_letter_code_can="ACGT" * 10)
        data["core/polymer_entity/1ABC/2"]["entity_poly"]["pdbx_seq_one_letter_code_can"] = SEQ + "X"
    client = structure_adapter(monkeypatch, tmp_path, changes=change)
    values = asyncio.run(client.fetch_structure("1ABC"))["sequences"]
    assert values[0]["verified"] is False and values[0]["entity_type"] == "unsupported_polymer"
    assert values[1]["verified"] is False
    assert values[1]["target_accessions"] == []
