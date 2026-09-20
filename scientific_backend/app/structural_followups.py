"""Public-sequence, exploratory CD19 isoform modeling through real NVIDIA NIM.

This compares two isolated monomers. It never qualifies CAR binding, target
retention, glycosylation, surface trafficking, splicing or patient response.
"""
from __future__ import annotations

import asyncio
import hashlib
import io
import json
import math
import os
from pathlib import Path
import re

import httpx
import numpy as np
from Bio.PDB import MMCIFParser
from Bio.Seq import Seq
from Bio.SeqUtils import seq1

from .config import ROOT

RECIPE = "cd19-exon2-structure"
SCOPE = "exploratory_public_isoform_structure"
SOURCE_ROOT = ROOT / "casepacks" / "sources" / "cd19-discovery"
AUTHOR = "https://raw.githubusercontent.com/mcortes-lopez/CD19_splicing_mutagenesis/edd69ccba3a193ca13ee66a5a4b191d980a940a1/minigene_annotation/"
SOURCE_SPECS = {
    "P15391.json": ("a000a6a2049d4fd263c8af16fe0c0e85f97293aaf3d76b9f61db88f196fb3545", "https://rest.uniprot.org/uniprotkb/P15391.json"),
    "CD19_WT.minigene.fa": ("0718f3e82821c6460294068a1ea2db6d26e707e60cd57500139836ae544223a0", AUTHOR + "CD19_WT.minigene.fa"),
    "CD19_WT.minigene.anno.gtf": ("6e1cc2ba37c7b159f403fd44487c958ecd1840b692f876bfc009292eb7096b55", AUTHOR + "CD19_WT.minigene.anno.gtf"),
}
LIMITATIONS = [
    "Exploratory predictions of isolated public-sequence CD19 ectodomains, not patient-specific constructs or a CAR-binder comparison.",
    "No glycans, membrane, CD81 or CAR binder are modeled; surface trafficking, epitope recognition and killing cannot be inferred.",
    "A structure predictor does not predict exon inclusion or prove a splicing-mediated resistance mechanism.",
    "One sample per isoform; confidence and aligned backbone displacement are model outputs, not measured accuracy, affinity or efficacy.",
]


def _hash(value):
    if not isinstance(value, bytes):
        value = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode()
    return hashlib.sha256(value).hexdigest()


def _save(path, value):
    """Flush intent/outcome before proceeding across a provider boundary."""
    payload = json.dumps(value, sort_keys=True, indent=2, ensure_ascii=False, allow_nan=False).encode()
    tmp = path.with_suffix(path.suffix + ".tmp")
    with tmp.open("wb") as handle:
        handle.write(payload); handle.flush(); os.fsync(handle.fileno())
    os.replace(tmp, path)
    fd = os.open(path.parent, os.O_RDONLY)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


def qualified_inputs():
    """Reproduce exon-to-protein mapping against independently pinned UniProt."""
    raw, sources = {}, []
    for name, (expected, url) in SOURCE_SPECS.items():
        path = SOURCE_ROOT / name
        if path.is_symlink() or path.stat().st_size > 200_000:
            raise ValueError("Structural reference exceeds the source contract")
        data = path.read_bytes()
        if _hash(data) != expected:
            raise ValueError("Structural reference changed: " + name)
        raw[name] = data.decode()
        sources.append({"name": name, "path": "sources/cd19-discovery/" + name,
                        "url": url, "sha256": expected, "bytes": len(data)})
    reference = json.loads(raw["P15391.json"])
    protein = reference["sequence"]["value"]
    if reference["primaryAccession"] != "P15391" or len(protein) != 556:
        raise ValueError("Unexpected canonical CD19 reference")
    domains = [(f["location"]["start"]["value"], f["location"]["end"]["value"])
               for f in reference["features"] if f["type"] == "Topological domain" and f["description"] == "Extracellular"]
    if domains != [(20, 291)]:
        raise ValueError("Extracellular boundary changed")
    dna = "".join(line.strip() for line in raw["CD19_WT.minigene.fa"].splitlines() if not line.startswith(">"))
    exons = sorted((int(c[3]), int(c[4])) for line in raw["CD19_WT.minigene.anno.gtf"].splitlines()
                   if line and not line.startswith("#") and (c := line.split("\t"))[2] == "exon")
    if exons != [(69, 218), (476, 742), (1041, 1244)]:
        raise ValueError("Author exon coordinates changed")
    wt_rna = "".join(dna[start-1:end] for start, end in exons)
    skip_rna = "".join(dna[start-1:end] for start, end in (exons[0], exons[2]))
    start = wt_rna.find("ATG")
    def translated(sequence):
        coding = sequence[start:]
        return str(Seq(coding[:len(coding)//3*3]).translate())
    wt_prefix, skip_prefix = translated(wt_rna), translated(skip_rna)
    if start != 62 or len(wt_prefix) != 186 or wt_prefix != protein[:186]:
        raise ValueError("Author minigene does not match canonical protein translation")
    if len(skip_prefix) != 97 or skip_prefix != protein[:29] + protein[118:186]:
        raise ValueError("Exon skipping does not reproduce the claimed in-frame deletion")
    wt, delta = protein[19:291], protein[19:29] + protein[118:291]
    return {"wild_type": wt, "exon2_deleted": delta, "sources": sources,
            "mapping": {"uniprot": "P15391", "sequence_version": reference["entryAudit"]["sequenceVersion"],
                        "extracellular_residues": [20, 291], "deleted_canonical_residues": [30, 118],
                        "author_exons_1based_inclusive": [list(e) for e in exons], "matched_translation_residues": 186,
                        "derivation": "Author exons 1+2+3 translate to the canonical CD19 prefix; exons 1+3 exactly remove residues 30–118 without a frameshift."}}


def catalog(case_id):
    if case_id not in {"cart-discovery", "cd19-car-t"}:
        return []
    return [{"id": RECIPE, "title": "Predict normal and exon-2-deleted CD19 structures",
             "kind": "bionemo_public_structure",
             "description": "Two real NVIDIA Boltz-2 monomer predictions from a verified public exon-to-protein mapping. Visualize the possible structural consequence; does not test splicing, binding or trafficking.",
             "input_sources": [{"path": "sources/cd19-discovery/" + name, "sha256": spec[0]} for name, spec in SOURCE_SPECS.items()],
             "prerequisites": ["NVIDIA credential or configured local NIM", "Pinned author exon annotation and canonical UniProt sequence pass exact translation checks"]}]


def _validate_cif(cif, sequence):
    if not isinstance(cif, str) or len(cif.encode()) > 10_000_000 or not cif.lstrip().startswith("data_"):
        raise ValueError("Invalid or oversized NVIDIA structure")
    structure = MMCIFParser(QUIET=True, auth_chains=False, auth_residues=False).get_structure("prediction", io.StringIO(cif))
    models = list(structure.get_models())
    chains = list(models[0]) if len(models) == 1 else []
    if len(chains) != 1 or chains[0].id != "A":
        raise ValueError("Expected exactly one monomer chain A")
    residues = list(chains[0])
    observed = "".join(seq1(r.resname, undef_code="X") for r in residues)
    if observed != sequence or [r.id[1] for r in residues] != list(range(1, len(sequence)+1)):
        raise ValueError("Predicted residue identities differ from the submitted sequence")
    if any("CA" not in r for r in residues) or any(not np.isfinite(a.coord).all() for a in structure.get_atoms()):
        raise ValueError("Incomplete backbone or invalid coordinates")
    points = np.array([r["CA"].coord for r in residues], dtype=float)
    return {"exact_sequence_match": True, "sequence_sha256": _hash(sequence.encode()),
            "residues": len(residues), "atom_count": len(list(structure.get_atoms())),
            "coordinates_finite": True, "alpha_carbon_coverage_complete": True}, points


async def execute(recipe_id, *, output_dir: Path, emit=None, cancelled=None):
    from . import providers as p
    if recipe_id != RECIPE:
        raise ValueError("Unknown structural follow-up")
    inputs = qualified_inputs()  # Validate every input before spending on any job.
    endpoint, hosted = p._endpoint()
    key = os.getenv("NGC_API_KEY") or os.getenv("NVIDIA_API_KEY")
    if hosted and not key:
        raise p.ProviderError("NVIDIA credential missing; no structure request sent", status="missing")
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    if (output_dir / "comparison.json").exists():
        raise p.ProviderError("A structural comparison intent already exists; inspect it instead of resubmitting", status="unknown")
    state = {"status": "running", "scope": SCOPE, "recipe_id": RECIPE, "created_at": p._now(),
             "mapping": inputs["mapping"], "input_sources": inputs["sources"], "jobs": [], "artifacts": [], "limitations": LIMITATIONS}
    _save(output_dir / "comparison.json", state)
    headers = {"Content-Type": "application/json", "Accept": "application/json"}
    if hosted:
        headers["Authorization"] = "Bearer " + key
    timeout = float(os.getenv("NIM_TIMEOUT_SECONDS", "300"))
    if not math.isfinite(timeout) or not 1 <= timeout <= 900:
        raise ValueError("NIM timeout must be 1–900 seconds")
    coordinates = {}
    for label in ("wild_type", "exon2_deleted"):
        p._check_cancelled(cancelled)
        sequence = inputs[label]
        directory = output_dir / label
        directory.mkdir(exist_ok=False)
        payload = {"polymers": [{"id": "A", "molecule_type": "protein", "sequence": sequence}],
                   "recycling_steps": 3, "sampling_steps": 50, "diffusion_samples": 1,
                   "step_scale": 1.638, "output_format": "mmcif"}
        job = {"label": label, "model": "mit/boltz2", "scope": SCOPE, "status": "intent_recorded",
               "sequence_sha256": _hash(sequence.encode()), "sequence_length": len(sequence),
               "request_sha256": _hash(payload), "created_at": p._now(), "artifacts": []}
        _save(directory / "request.json", payload)
        _save(directory / "job.json", job)
        state["jobs"].append(job)
        _save(output_dir / "comparison.json", state)
        try:
            await p._emit(emit, "bionemo", "Predicting CD19 " + label.replace("_", " "),
                          f"{len(sequence)} source-qualified amino acids; one real Boltz-2 monomer request.", "running")
            job.update(status="dispatched", dispatched_at=p._now())
            _save(directory / "job.json", job)
            async def submit():
                async with httpx.AsyncClient(timeout=httpx.Timeout(timeout, connect=15), follow_redirects=False) as client:
                    async with client.stream("POST", endpoint, headers=headers, json=payload) as response:
                        job.update(http_status=response.status_code,
                                   request_id=response.headers.get("nvcf-reqid") or response.headers.get("x-request-id"))
                        chunks, size = [], 0
                        async for chunk in response.aiter_bytes():
                            size += len(chunk)
                            if size > 10_000_000:
                                raise ValueError("NVIDIA response exceeds 10 MB")
                            chunks.append(chunk)
                        return b"".join(chunks)
            raw = await p._bounded(submit(), cancelled, timeout + 5)
            text = p._redact(raw.decode("utf-8"))
            (directory / "response.txt").write_text(text)
            job.update(response_sha256=_hash(text.encode()), response_received_at=p._now())
            if job["http_status"] == 202:
                job.update(status="pending", detail="Vendor accepted the job; preserve request ID without automatic resubmission.")
                state["status"] = "pending"
                break
            if job["http_status"] != 200:
                raise p.ProviderError(f"NVIDIA returned HTTP {job['http_status']}")
            result = json.loads(text)
            structures, scores = result.get("structures"), result.get("confidence_scores")
            if not isinstance(structures, list) or len(structures) != 1 or not isinstance(scores, list) or len(scores) != 1:
                raise ValueError("Expected one returned structure and confidence score")
            score = scores[0]
            if type(score) not in (int, float) or not math.isfinite(score) or not 0 <= score <= 1:
                raise ValueError("Invalid NVIDIA confidence")
            if structures[0].get("format") != "mmcif":
                raise ValueError("Expected mmCIF format")
            cif = structures[0]["structure"]
            validation, coordinates[label] = _validate_cif(cif, sequence)
            artifact_path = directory / "prediction.cif"
            artifact_path.write_text(cif)
            artifact = {"name": label + "_prediction.cif", "path": str(artifact_path.resolve()),
                        "sha256": _hash(cif.encode()), "media_type": "chemical/x-mmcif", "label": label,
                        "model": "mit/boltz2", "request_id": job.get("request_id"), "confidence_score": score, "scope": SCOPE}
            job.update(status="completed", validation=validation, confidence_score=score,
                       artifacts=[artifact], finished_at=p._now())
            state["artifacts"].append(artifact)
            await p._emit(emit, "bionemo", "NVIDIA CD19 structure validated", label.replace("_", " ") + ": exact sequence and finite complete backbone verified.")
        except BaseException as exc:
            unknown = isinstance(exc, (asyncio.CancelledError, TimeoutError, httpx.TransportError)) or getattr(exc, "status", None) == "unknown"
            job.update(status="unknown" if unknown else "failed", detail=p._redact(str(exc))[:500], finished_at=p._now())
            state["status"] = job["status"]
            if isinstance(exc, asyncio.CancelledError):
                raise
            break
        finally:
            _save(directory / "job.json", job)
            _save(output_dir / "comparison.json", state)
    if len(coordinates) == 2:
        common = list(range(10)) + list(range(99, 272))
        fixed = coordinates["wild_type"][common]
        moving = coordinates["exon2_deleted"]
        fixed, moving = fixed - fixed.mean(0), moving - moving.mean(0)
        u, _, vt = np.linalg.svd(moving.T @ fixed)
        correction = np.diag([1., 1., float(np.linalg.det(u @ vt))])
        aligned = moving @ (u @ correction @ vt)
        rmsd = float(np.sqrt(np.mean(np.sum((aligned - fixed) ** 2, axis=1))))
        state.update(status="completed", comparison={"aligned_shared_backbone_rmsd_angstrom": rmsd,
                      "matched_residues": len(common), "method": "Least-squares proper rotation of 183 shared C-alpha positions; all matched positions, no outlier removal.",
                      "interpretation": "Difference between two predicted structures, not measured mutation effect or experimental accuracy."})
        values = {"structural_recipe_id": RECIPE, "scope": SCOPE, "recipe_version": "1.0.0",
                  "input_sources": inputs["sources"], "mapping": inputs["mapping"], "comparison": state["comparison"],
                  "predictions": [{k: j[k] for k in ("label", "model", "request_id", "status", "sequence_sha256", "sequence_length", "confidence_score", "validation")} for j in state["jobs"]],
                  "artifact_hashes": [a["sha256"] for a in state["artifacts"]], "limitations": LIMITATIONS,
                  "binding_tested": False, "splicing_predicted": False, "experimental_validation": False}
        evidence = {"id": "NVIDIA-CD19-" + _hash(values)[:16], "title": "Predicted CD19 normal and exon-2-deleted ectodomains",
                    "kind": "prediction", "summary": f"Two real NVIDIA Boltz-2 monomer structures passed exact sequence checks (272 and 183 residues). Shared-backbone alignment RMSD={rmsd:.2f} Å across 183 positions. This is exploratory structural context, not a test of binding, trafficking or therapy response.",
                    "source": {"name": "NVIDIA BioNeMo Boltz-2 with pinned public CD19 sequences", "url": "https://build.nvidia.com/mit/boltz2",
                               "locator": "Two one-shot monomer calls; provider request IDs, sequence/source and artifact hashes in values", "sha256": _hash(values)}, "values": values}
        state["evidence"] = evidence
    state["finished_at"] = p._now()
    _save(output_dir / "comparison.json", state)
    return state


def validate_evidence(record):
    values = record.get("values", {})
    if values.get("structural_recipe_id") != RECIPE or values.get("scope") != SCOPE or record.get("kind") != "prediction":
        raise ValueError("Unregistered structural result")
    if any(values.get(key) is not False for key in ("binding_tested", "splicing_predicted", "experimental_validation")):
        raise ValueError("Structural prediction scope was overstated")
    if record.get("source", {}).get("sha256") != _hash(values):
        raise ValueError("Structural evidence content hash mismatch")
    inputs = qualified_inputs()
    if values.get("input_sources") != inputs["sources"] or values.get("mapping") != inputs["mapping"]:
        raise ValueError("Structural input source versions differ")
    predictions = values.get("predictions", [])
    if [p.get("label") for p in predictions] != ["wild_type", "exon2_deleted"] or len(values.get("artifact_hashes", [])) != 2:
        raise ValueError("Structural comparison requires both validated members")
    if any(not isinstance(h, str) or not re.fullmatch(r"[a-f0-9]{64}", h) for h in values["artifact_hashes"]):
        raise ValueError("Invalid structural artifact identity")
    for prediction in predictions:
        sequence = inputs[prediction["label"]]
        validation = prediction.get("validation", {})
        if prediction.get("status") != "completed" or prediction.get("sequence_sha256") != _hash(sequence.encode()):
            raise ValueError("Unverified structural prediction")
        if validation.get("exact_sequence_match") is not True or validation.get("residues") != len(sequence):
            raise ValueError("Structural sequence qualification failed")
        if validation.get("sequence_sha256") != _hash(sequence.encode()) or any(validation.get(key) is not True for key in ("coordinates_finite", "alpha_carbon_coverage_complete")):
            raise ValueError("Structural coordinate qualification failed")
        confidence = prediction.get("confidence_score")
        if type(confidence) not in (int, float) or not math.isfinite(confidence) or not 0 <= confidence <= 1 or prediction.get("model") != "mit/boltz2":
            raise ValueError("Invalid structural model or confidence receipt")
        request_id = prediction.get("request_id")
        if request_id is not None and (not isinstance(request_id, str) or not re.fullmatch(r"[A-Za-z0-9._:-]{1,200}", request_id)):
            raise ValueError("Invalid provider request identity")
    return True
