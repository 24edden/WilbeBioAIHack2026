"""Bounded public sequence retrieval through the installed OpenAI source skills.

Only server-constructed public queries reach the pinned skill scripts. Models
cannot supply a URL, credentials, output path, executable or sequence bytes.
"""
from __future__ import annotations

import asyncio
import hashlib
import json
import os
from pathlib import Path
import re
import sys
import uuid

from .config import RUNTIME
from .scientific_skills import verify_life_sciences_runtime
from .store import now

AA = frozenset("ACDEFGHIKLMNPQRSTVWY")


def _hash(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _query(value: str) -> str:
    if not isinstance(value, str) or not 2 <= len(value.strip()) <= 160:
        raise ValueError("Use a short public protein, gene or binder query.")
    value = value.strip()
    if any(ord(c) < 32 or ord(c) == 127 for c in value) or any(x in value.lower() for x in ("http:", "https:", "@", "\\")):
        raise ValueError("Public sequence searches accept scientific names, not links or private identifiers.")
    return value


def _sequence_record(sequence, *, label, url, locator, source_sha256, entity_type, target_accessions, provenance):
    sequence = re.sub(r"\s+", "", str(sequence or "")).upper()
    verified = 20 <= len(sequence) <= 3000 and set(sequence) <= AA
    checksum = _hash(sequence.encode())
    return {"id": "public-sequence-" + _hash((url + "|" + locator + "|" + checksum).encode())[:24],
            "label": label, "sequence": sequence, "length": len(sequence), "sequence_sha256": checksum,
            "verified": verified, "source_url": url, "source_locator": locator, "source_sha256": source_sha256,
            "entity_type": entity_type, "target_accessions": target_accessions, "provenance": provenance,
            "qualification": "Exact deposited canonical sequence retrieved; construct and use require scientific review." if verified else
                             "Sequence is outside supported length or contains unresolved/nonstandard residues; not eligible for autofill."}


class SequenceSources:
    def __init__(self, emit=None, cancelled=None, artifact_dir: Path | None = None):
        self.emit, self.cancelled = emit, cancelled
        self.sources: list[dict] = []
        self.receipts: list[dict] = []
        self.artifact_dir = artifact_dir or RUNTIME / "sequence-sources" / uuid.uuid4().hex
        self._cache = {}
        self._calls = 0

    def _check(self):
        if self.cancelled and self.cancelled():
            raise asyncio.CancelledError()

    async def _request(self, skill_id, base_url, path, **kwargs):
        self._check()
        method = kwargs.get("method", "GET")
        allowed = (
            skill_id == "uniprot-skill" and base_url == "https://rest.uniprot.org" and method == "GET"
            and re.fullmatch(r"uniprotkb/(?:search|[A-Z0-9]{6,10}(?:-\d{1,2})?)", path)
        ) or (
            skill_id == "rcsb-pdb-skill" and base_url == "https://search.rcsb.org/rcsbsearch/v2"
            and path == "query" and method == "POST"
        ) or (
            skill_id == "rcsb-pdb-skill" and base_url == "https://data.rcsb.org/rest/v1" and method == "GET"
            and re.fullmatch(r"core/(?:entry/[A-Z0-9]{4}|polymer_entity/[A-Z0-9]{4}/\d{1,3})", path)
        )
        if not allowed or set(kwargs) - {"method", "params", "json_body", "response_format"}:
            raise ValueError("Public sequence retrieval is restricted to the registered UniProt and RCSB routes.")
        empty_search_allowed = base_url == "https://search.rcsb.org/rcsbsearch/v2" and path == "query"
        if kwargs.get("response_format", "json") != "json" and not (empty_search_allowed and kwargs["response_format"] == "text"):
            raise ValueError("Only the public RCSB search route accepts text response handling.")
        # All arguments here originate in the four wrappers below, never a raw
        # model tool object. Source scripts independently enforce source hosts.
        key = json.dumps([skill_id, base_url, path, kwargs], sort_keys=True)
        if key in self._cache:
            return self._cache[key]
        if self._calls >= 100:
            raise ValueError("This sequence search reached its public-lookup bound; use the retrieved records or report the gap.")
        self._calls += 1
        root = verify_life_sciences_runtime()
        self.artifact_dir.mkdir(parents=True, exist_ok=True)
        identifier = uuid.uuid4().hex
        raw_path = self.artifact_dir / (identifier + ".json")
        payload = {"base_url": base_url, "path": path, "response_format": "json", "max_items": 10,
                   "timeout_sec": 25, "save_raw": True, "raw_output_path": str(raw_path), **kwargs}
        receipt = {"id": identifier, "skill_id": skill_id, "method": payload.get("method", "GET"),
                   "endpoint": base_url + "/" + path, "request_sha256": _hash(key.encode()),
                   "started_at": now(), "status": "started"}
        self.receipts.append(receipt)
        # The source client needs no vendor credentials or private environment.
        environment = {k: v for k, v in os.environ.items() if k in {"PATH", "SYSTEMROOT", "SSL_CERT_FILE", "SSL_CERT_DIR", "LANG"}}
        process, communication = None, None
        try:
            process = await asyncio.create_subprocess_exec(sys.executable, str(root / "skills" / skill_id / "scripts/rest_request.py"),
                        stdin=asyncio.subprocess.PIPE, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE, env=environment)
            communication = asyncio.create_task(process.communicate(json.dumps(payload).encode()))
            for _ in range(180):
                self._check()
                done, _ = await asyncio.wait({communication}, timeout=.25)
                if done:
                    break
            else:
                raise TimeoutError("Public sequence lookup exceeded its time bound.")
            output, _ = await communication
            if len(output) > 2_000_000:
                raise ValueError("Public source response exceeded its compact-output bound.")
            envelope = json.loads(output)
            if process.returncode != 0 or not envelope.get("ok"):
                raise ValueError("Public sequence source lookup failed: " + str(envelope.get("error", {}).get("code", "source_error")))
            if not raw_path.is_file() or raw_path.stat().st_size > 5_000_000:
                raise ValueError("Public sequence source exceeded its record-size bound.")
            raw = raw_path.read_bytes()
            # The installed source client handles an empty HTTP204 correctly in
            # text mode. A no-hit search is useful negative discovery, not an
            # invented successful record or a swallowed source error.
            if empty_search_allowed and envelope.get("status_code") == 204 and not raw.strip():
                data = {"result_set": [], "total_count": 0}
            else:
                data = json.loads(raw)
            if not isinstance(data, dict):
                raise ValueError("Public source did not return an object record.")
            receipt.update(status="completed", finished_at=now(), source_sha256=_hash(raw),
                           http_status=envelope.get("status_code"), bytes=len(raw),
                           sources=envelope.get("sources", []), checked_sources=envelope.get("checked_sources", []))
            self._cache[key] = (data, receipt)
            return data, receipt
        except BaseException:
            receipt.update(status="failed", finished_at=now())
            raise
        finally:
            if process is not None and process.returncode is None:
                process.kill()
                await process.wait()
            if communication is not None and not communication.done():
                communication.cancel()
            if communication is not None:
                await asyncio.gather(communication, return_exceptions=True)

    def _remember(self, record):
        if not any(x["id"] == record["id"] for x in self.sources):
            self.sources.append(record)
        return record

    async def search_uniprot(self, query: str):
        data, receipt = await self._request("uniprot-skill", "https://rest.uniprot.org", "uniprotkb/search",
            params={"query": _query(query), "size": 10, "format": "json", "fields": "accession,id,protein_name,gene_names,organism_name,length"})
        return {"records": data.get("results", [])[:10], "source_receipt_id": receipt["id"], "note": "Search identities only; fetch an accession for exact sequence."}

    async def fetch_uniprot(self, accession: str):
        if not isinstance(accession, str) or not re.fullmatch(r"[A-Z0-9]{6,10}(?:-\d{1,2})?", accession):
            raise ValueError("Supply a UniProt accession returned by the source search.")
        data, receipt = await self._request("uniprot-skill", "https://rest.uniprot.org", "uniprotkb/" + accession, params={"format": "json"})
        if data.get("primaryAccession") != accession:
            raise ValueError("Returned UniProt accession does not match the requested identity.")
        description = data.get("proteinDescription", {}).get("recommendedName", {}).get("fullName", {}).get("value") or data.get("uniProtkbId") or accession
        return self._remember(_sequence_record(data.get("sequence", {}).get("value"), label=description,
            url="https://www.uniprot.org/uniprotkb/" + accession, locator="UniProtKB " + accession + "; full canonical sequence",
            source_sha256=receipt["source_sha256"], entity_type="protein", target_accessions=[accession],
            provenance={"provider": "UniProt", "accession": accession, "entry_audit": data.get("entryAudit", {}),
                        "organism": data.get("organism", {}), "gene_names": data.get("genes", []), "features": data.get("features", [])[:30],
                        "source_receipt_id": receipt["id"], "retrieved_at": receipt["finished_at"]}))

    async def search_structures(self, query: str):
        data, receipt = await self._request("rcsb-pdb-skill", "https://search.rcsb.org/rcsbsearch/v2", "query", method="POST",
            response_format="text",
            json_body={"query": {"type": "terminal", "service": "full_text", "parameters": {"value": _query(query)}},
                       "return_type": "entry", "request_options": {"paginate": {"start": 0, "rows": 10}}})
        records = []
        for match in data.get("result_set", [])[:10]:
            identifier = match.get("identifier", "")
            if not re.fullmatch(r"[0-9A-Za-z]{4}", identifier):
                continue
            entry, entry_receipt = await self._request("rcsb-pdb-skill", "https://data.rcsb.org/rest/v1", "core/entry/" + identifier.upper())
            if entry.get("rcsb_id") != identifier.upper():
                raise ValueError("Returned PDB entry identity does not match the requested record.")
            records.append({"pdb_id": identifier.upper(), "title": entry.get("struct", {}).get("title"),
                            "methods": entry.get("exptl", []), "source_url": "https://www.rcsb.org/structure/" + identifier.upper(),
                            "citation": entry.get("rcsb_primary_citation", {}), "source_receipt_id": entry_receipt["id"]})
        return {"records": records, "total_count": data.get("total_count"), "source_receipt_id": receipt["id"]}

    async def fetch_structure(self, pdb_id: str):
        if not isinstance(pdb_id, str) or not re.fullmatch(r"[0-9A-Za-z]{4}", pdb_id):
            raise ValueError("Supply a four-character PDB entry identifier.")
        pdb_id = pdb_id.upper()
        entry, receipt = await self._request("rcsb-pdb-skill", "https://data.rcsb.org/rest/v1", "core/entry/" + pdb_id)
        if entry.get("rcsb_id") != pdb_id:
            raise ValueError("Returned PDB entry identity does not match the requested record.")
        ids = entry.get("rcsb_entry_container_identifiers", {}).get("polymer_entity_ids", [])
        if not ids or len(ids) > 8:
            raise ValueError("Select a deposited complex with one to eight polymer entities.")
        polymers, accessions = [], []
        for entity_id in ids:
            if not re.fullmatch(r"\d{1,3}", str(entity_id)):
                raise ValueError("Invalid deposited polymer entity identifier.")
            data, source = await self._request("rcsb-pdb-skill", "https://data.rcsb.org/rest/v1", f"core/polymer_entity/{pdb_id}/{entity_id}")
            identifiers = data.get("rcsb_polymer_entity_container_identifiers", {})
            if (data.get("rcsb_id") != f"{pdb_id}_{entity_id}" or identifiers.get("entry_id") != pdb_id
                    or str(identifiers.get("entity_id")) != str(entity_id)):
                raise ValueError("Returned PDB polymer identity does not match the requested entry and entity.")
            refs = [x.get("database_accession") for x in identifiers.get("reference_sequence_identifiers", []) if x.get("database_name") == "UniProt"]
            label = data.get("rcsb_polymer_entity", {}).get("pdbx_description", "Unnamed polymer")
            lower = label.lower()
            binder = bool(re.search(r"scfv|single[ -]chain.*(?:fragment|variable)|nanobody|vhh|single[ -]domain antibody", lower))
            chain = bool(re.search(r"(?:heavy|light) chain|\bfab\b|immunoglobulin|antibody", lower))
            kind = "single_chain_binder" if binder else "antibody_chain" if chain else "protein"
            polymer_type = data.get("entity_poly", {}).get("type")
            supported_protein = polymer_type == "polypeptide(L)"
            if not supported_protein:
                kind = "unsupported_polymer"
            if kind == "protein":
                accessions.extend(x for x in refs if isinstance(x, str))
            record = _sequence_record(data.get("entity_poly", {}).get("pdbx_seq_one_letter_code_can"),
                label=f"{pdb_id} entity {entity_id}: {label}", url="https://www.rcsb.org/structure/" + pdb_id,
                locator=f"RCSB {pdb_id} polymer entity {entity_id}; deposited canonical construct; chains " + ",".join(identifiers.get("auth_asym_ids", [])),
                source_sha256=source["source_sha256"], entity_type=kind, target_accessions=[],
                provenance={"provider": "RCSB PDB", "pdb_id": pdb_id, "entity_id": str(entity_id),
                            "description": label, "entry_title": entry.get("struct", {}).get("title"), "chain_ids": identifiers.get("auth_asym_ids", []),
                            "own_uniprot_accessions": refs, "methods": entry.get("exptl", []), "entry_version": entry.get("rcsb_accession_info", {}),
                            "polymer_type": polymer_type,
                            "citation": entry.get("rcsb_primary_citation", {}), "source_receipt_id": source["id"], "retrieved_at": source["finished_at"]})
            if not supported_protein:
                record.update(verified=False, qualification="Deposited polymer is not a source-qualified L-amino-acid protein; excluded from molecular input selection.")
            polymers.append(record)
        for record in polymers:
            record["target_accessions"] = sorted(set(record["provenance"]["own_uniprot_accessions"] if record["entity_type"] == "protein" else accessions))
            self._remember(record)
        return {"pdb_id": pdb_id, "title": entry.get("struct", {}).get("title"), "source_url": "https://www.rcsb.org/structure/" + pdb_id,
                "sequences": polymers, "note": "Co-deposition supplies complex context, not proof of a patient construct, improved binding or target retention."}
