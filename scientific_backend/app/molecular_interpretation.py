"""Read-only, versioned interpretation of accepted molecular artifacts.

This derives facts from existing files; it neither executes a provider nor edits a
run. Exact amino acids are copied only from hash/receipt-matched structures.
"""
from __future__ import annotations

import hashlib
import io
import json
import math
from pathlib import Path
import re

import numpy as np
from Bio.PDB import MMCIFParser
from Bio.PDB.MMCIF2Dict import MMCIF2Dict
from Bio.PDB.PDBExceptions import PDBConstructionException
from Bio.SeqUtils import seq1

SCHEMA = "molecular-interpretation/1.0"
MAX_FILE_BYTES = 10_000_000
AA = set("ACDEFGHIKLMNPQRSTVWY")
COMMON_LIMITS = [
    "This is a new read-only audit of saved artifacts; prior decisions and evidence remain unchanged.",
    "Model confidence is not the probability of binding, resistance, clinical causation or experimental accuracy.",
    "One model per input does not quantify sampling uncertainty; different sequences can have different model errors.",
    "A target sequence or predicted target fold does not establish surface target retention or supply a CAR-binding-domain sequence.",
]


def _hash(value):
    if not isinstance(value, bytes):
        value = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode()
    return hashlib.sha256(value).hexdigest()


def _read(path: Path) -> bytes:
    # Bound bytes before parsing and reject symlink traversal, including parents.
    if any(p.is_symlink() for p in (path, *path.parents)):
        raise ValueError("Artifact path contains a symbolic link")
    if not path.is_file() or not 0 < path.stat().st_size <= MAX_FILE_BYTES:
        raise ValueError("Artifact is missing, empty or exceeds the read bound")
    return path.read_bytes()


def _artifact_path(run_id, artifact, artifact_root, artifact_paths):
    checksum = artifact.get("sha256")
    if not isinstance(checksum, str) or not re.fullmatch(r"[a-f0-9]{64}", checksum):
        raise ValueError("Artifact has no valid SHA256 identity")
    if checksum in artifact_paths:
        path = Path(artifact_paths[checksum]).absolute()
    elif artifact_root is not None:
        root = Path(artifact_root).absolute()
        url = artifact.get("url", "")
        prefix = f"/api/runs/{run_id}/artifacts/"
        if not isinstance(url, str) or not url.startswith(prefix):
            raise ValueError("Artifact is not registered to this run")
        suffix = url[len(prefix):]
        if not suffix or any(p in {"", ".", ".."} for p in suffix.split("/")) or "%" in suffix or "\\" in suffix:
            raise ValueError("Unsafe artifact locator")
        path = root / "artifacts" / suffix
        if not path.resolve().is_relative_to(root.resolve() / "artifacts"):
            raise ValueError("Artifact leaves the runtime artifact directory")
    else:
        raise ValueError("Saved artifact files were not supplied")
    data = _read(path)
    if _hash(data) != checksum:
        raise ValueError("Artifact bytes do not match the accepted SHA256")
    return path, data


def _rows(cif, prefix, names):
    columns = [cif.get(prefix + name, []) for name in names]
    if not columns or any(not isinstance(c, list) for c in columns) or len({len(c) for c in columns}) != 1:
        raise ValueError("Malformed ModelCIF table")
    return list(zip(*columns))


def _parse(data):
    text = data.decode("utf-8")
    if not text.lstrip().startswith("data_"):
        raise ValueError("Artifact is not mmCIF")
    cif = MMCIF2Dict(io.StringIO(text))
    structure = MMCIFParser(QUIET=True, auth_chains=False, auth_residues=False).get_structure("audit", io.StringIO(text))
    models = list(structure)
    if len(models) != 1:
        raise ValueError("Exactly one structural model is required")
    chains = {}
    for chain in models[0]:
        residues = list(chain)
        sequence = "".join(seq1(r.resname, undef_code="X") for r in residues)
        if not 1 <= len(sequence) <= 4096 or set(sequence) - AA or any("CA" not in r for r in residues):
            raise ValueError("Expected complete standard-amino-acid backbone")
        if [r.id[1] for r in residues] != list(range(1, len(sequence) + 1)):
            raise ValueError("Residue numbering must be complete and start at one")
        points = np.array([r["CA"].coord for r in residues], dtype=float)
        if any(not np.isfinite(a.coord).all() for r in residues for a in r):
            raise ValueError("Nonfinite coordinates")
        chains[str(chain.id)] = {"sequence": sequence, "coordinates": points}
    if not 1 <= len(chains) <= 12:
        raise ValueError("No bounded protein assembly is present")
    return cif, chains


def _confidence(cif, chain_id, sequence):
    """Read declared local metrics; never assume that generic B factors are pLDDT."""
    try:
        definitions = _rows(cif, "_ma_qa_metric.", ("id", "type", "mode"))
        kinds = {i: kind for i, kind, mode in definitions if kind.lower() in {"plddt", "plddt in [0,1]", "plddt all-atom", "plddt all-atom in [0,1]"} and mode.lower() == "local"}
        ids = list(kinds)
        if len(ids) != 1:
            raise ValueError("No unique declared local pLDDT metric")
        rows = _rows(cif, "_ma_qa_metric_local.", ("model_id", "label_asym_id", "label_seq_id", "label_comp_id", "metric_id", "metric_value"))
        found = {}
        for model, chain, position, residue, metric, value in rows:
            if chain != chain_id or metric != ids[0]:
                continue
            index, score = int(position), float(value)
            if model != "1" or index in found or not 1 <= index <= len(sequence):
                raise ValueError("Local confidence identity/coverage mismatch")
            if seq1(residue, undef_code="X") != sequence[index-1] or not math.isfinite(score) or not 0 <= score <= 100:
                raise ValueError("Local confidence values or residues are invalid")
            found[index] = score
        if "[0,1]" in kinds[ids[0]] and any(v > 1 for v in found.values()):
            raise ValueError("Local confidence exceeds its declared normalized range")
        if set(found) != set(range(1, len(sequence)+1)):
            raise ValueError("Local confidence does not cover the complete sequence")
        values = [found[i] for i in range(1, len(sequence)+1)]
        # Expose the producer's encoding rather than silently normalizing it.
        native_scale = "0..1 observed values" if max(values) <= 1 else "0..100 observed values"
        ambiguous = max(values) <= 1 and "[0,1]" not in kinds[ids[0]]
        scale_note = ("The CIF declares generic pLDDT (dictionary range 0..100) but observed values all lie in 0..1. No normalization or standard 70-pLDDT claim is made." if ambiguous else "Metric declaration and observed range are compatible; no rescaling applied.")
        return {"status": "verified", "metric": "pLDDT", "source_field": "_ma_qa_metric_local.metric_value",
                "native_scale": native_scale, "normalization_applied": False, "metric_id": ids[0],
                "declared_metric_type": kinds[ids[0]], "scale_ambiguous": ambiguous, "scale_note": scale_note,
                "mean": float(np.mean(values)), "min": min(values), "max": max(values),
                "values": values, "regions": [],
                "interpretation": "Model-declared local structural confidence, not calibrated evidence of a biological effect."}
    except (ValueError, TypeError, KeyError) as exc:
        return {"status": "unavailable", "reason": str(exc), "values": [], "regions": [],
                "interpretation": "No per-residue confidence claim or confidence-filtered fit is made."}


def _request_audit(path, prediction, artifact, chains):
    """Job hash anchors request bytes; paths and arbitrary JSON fields stay private."""
    try:
        job = json.loads(_read(path.parent / "job.json"))
        request = json.loads(_read(path.parent / "request.json"))
        if job.get("status") != "completed" or job.get("http_status") != 200 or job.get("request_id") != prediction.get("request_id"):
            raise ValueError("Request job does not match the completed accepted receipt")
        if job.get("model") != prediction.get("model") or job.get("sequence_sha256") != prediction.get("sequence_sha256"):
            raise ValueError("Job model/sequence identity mismatch")
        if artifact["sha256"] not in {a.get("sha256") for a in job.get("artifacts", []) if isinstance(a, dict)}:
            raise ValueError("Job does not identify the accepted artifact")
        if job.get("request_sha256") != _hash(request):
            raise ValueError("Submitted request content hash mismatch")
        polymers = request.get("polymers", [])
        submitted = {p.get("id"): p.get("sequence") for p in polymers if isinstance(p, dict) and p.get("molecule_type") == "protein"}
        if len(submitted) != len(polymers) or submitted != {k: v["sequence"] for k, v in chains.items()}:
            raise ValueError("Request polymer identities differ from the accepted structure")
        scalar_names = ("recycling_steps", "sampling_steps", "diffusion_samples", "step_scale", "output_format", "seed", "random_seed", "without_potentials", "write_full_pae", "write_full_pde")
        settings = {k: v for k, v in request.items() if k in scalar_names and type(v) in (str, int, float, bool)}
        shape = {k: v for k, v in request.items() if k != "polymers"}
        shape["polymers"] = [{k: v for k, v in p.items() if k != "sequence"} for p in polymers]
        return {"status": "verified", "request_sha256": job["request_sha256"],
                "nonsequence_settings_sha256": _hash(shape), "settings": settings,
                "model_version": job.get("model_version") or "not recorded in this job",
                "msa_supplied": any(bool(p.get("msa")) for p in polymers),
                "templates_supplied": any(bool(p.get("structural_templates")) for p in polymers),
                "modifications_supplied": any(bool(p.get("modifications")) for p in polymers),
                "ligands_supplied": bool(request.get("ligands")),
                "limits": ["Unspecified server defaults and random seeds cannot be recovered from submitted fields."]}
    except (OSError, ValueError, TypeError, KeyError) as exc:
        # Do not leak file locations in exception messages.
        reason = str(exc) if isinstance(exc, ValueError) and not isinstance(exc, json.JSONDecodeError) else "Saved request/job records are missing or malformed"
        return {"status": "unavailable", "reason": reason, "settings": {}, "model_version": "unverified"}


def _fit(fixed, moving):
    if len(fixed) < 3:
        raise ValueError("At least three matched residues are required for a fit")
    fixed = fixed - fixed.mean(axis=0)
    moving = moving - moving.mean(axis=0)
    if min(np.linalg.matrix_rank(fixed), np.linalg.matrix_rank(moving)) < 2:
        raise ValueError("Matched points are degenerate")
    u, _, vt = np.linalg.svd(moving.T @ fixed)
    rotation = u @ np.diag([1., 1., float(np.linalg.det(u @ vt))]) @ vt
    displacement = np.linalg.norm(moving @ rotation - fixed, axis=1)
    return {"matched_residues": len(fixed), "rmsd_angstrom": float(np.sqrt(np.mean(displacement**2))),
            "median_displacement_angstrom": float(np.median(displacement)),
            "max_displacement_angstrom": float(displacement.max())}


def _alignment(values, parsed, predictions):
    """Sensitivity fits for a source-mapped, exact in-frame deletion pair only."""
    unavailable = {"status": "unavailable", "reason": "No qualified exact internal-deletion correspondence was available"}
    if len(parsed) != 2 or any(len(x["chains"]) != 1 for x in parsed):
        return unavailable
    reference, changed = sorted(parsed, key=lambda x: len(next(iter(x["chains"].values()))["sequence"]), reverse=True)
    refchain = next(iter(reference["chains"].values()))
    altchain = next(iter(changed["chains"].values()))
    ref, alt = refchain["sequence"], altchain["sequence"]
    mapping = values.get("mapping", {})
    bounds, deletion = mapping.get("extracellular_residues"), mapping.get("deleted_canonical_residues")
    if not isinstance(bounds, list) or len(bounds) != 2 or not isinstance(deletion, list) or len(deletion) != 2:
        return unavailable
    if any(type(x) is not int for x in [*bounds, *deletion]):
        return unavailable
    start, end = bounds; ds, de = deletion
    if len(ref) != end-start+1 or not start < ds <= de < end or ref[:ds-start]+ref[de-start+1:] != alt:
        return unavailable
    left = ds-start
    common = list(range(left)) + list(range(de-start+1, len(ref)))
    fixed, moving = refchain["coordinates"][common], altchain["coordinates"]
    fits = []
    def add(name, indices, reason):
        result = {"name": name, "selection": reason, "selected_residues": len(indices),
                  "reference_positions_1based": [common[i]+1 for i in indices],
                  "comparison_positions_1based": [i+1 for i in indices]}
        try:
            result.update(status="computed", **_fit(fixed[indices], moving[indices]))
        except ValueError as exc:
            result.update(status="unavailable", reason=str(exc))
        fits.append(result)
    add("all_shared_residues", list(range(len(alt))), "All sequence-corresponding C-alpha positions; no outlier removal")
    add("before_deletion", list(range(left)), f"Shared canonical residues {start}–{ds-1}; separately fitted")
    add("after_deletion", list(range(left, len(alt))), f"Shared canonical residues {de+1}–{end}; separately fitted")
    # Fixed protocol: report every third rather than selecting visually favorable domains.
    for n, indices in enumerate(np.array_split(np.arange(len(alt)), 3), start=1):
        add(f"shared_sequence_third_{n}", [int(i) for i in indices], "Predefined consecutive third of the shared sequence; separately fitted, not an annotated protein domain")
    by_label = {p["label"]: p for p in predictions}
    ref_conf = by_label[reference["label"]]["confidence"]
    alt_conf = by_label[changed["label"]]["confidence"]
    if ref_conf.get("status") == alt_conf.get("status") == "verified" and ref_conf["native_scale"] == alt_conf["native_scale"]:
        scale = 1 if ref_conf["native_scale"].startswith("0..1 ") else 100
        qualified = [i for i, ri in enumerate(common) if ref_conf["values"][ri] >= .7*scale and alt_conf["values"][i] >= .7*scale]
        add("both_raw_local_metric_ge_0_7_or_70", qualified,
            f"Both raw local pLDDT fields >= {0.7*scale:g}; predefined descriptive cutoff, not a validated accuracy threshold or scale conversion")
        fits[-1]["raw_metric_cutoff"] = .7*scale
        fits[-1]["scale_ambiguous"] = ref_conf["scale_ambiguous"] or alt_conf["scale_ambiguous"]
        for item, conf, regions in ((reference, ref_conf, [("before_deletion", 0, left), ("deleted_region", left, de-start+1), ("after_deletion", de-start+1, len(ref))]),
                                    (changed, alt_conf, [("before_deletion", 0, left), ("after_deletion", left, len(alt))])):
            for name, lo, hi in regions:
                vals = conf["values"][lo:hi]
                conf["regions"].append({"name": name, "sequence_positions_1based": [lo+1, hi], "residues": len(vals),
                                        "mean": float(np.mean(vals)), "min": min(vals), "max": max(vals)})
    return {"status": "computed", "reference_label": reference["label"], "comparison_label": changed["label"],
            "canonical_mapping": mapping, "fits": fits,
            "method": "Proper-rotation least-squares Kabsch fits on exact sequence-corresponding C-alpha atoms. Every subset is fitted independently; no fitted-point trimming.",
            "interpretation": "Fit dependence distinguishes local predicted shape from a large whole-construct displacement. It does not identify an epitope or validate either fold.",
            "limitations": ["These are post hoc descriptive sensitivity checks, not independent predictions or hypothesis tests.",
                            "Different residue subsets estimate different geometric quantities; small subset RMSD does not rescue a low-confidence global model.",
                            "Missing domain/epitope annotations and PAE prevent an interface-specific or inter-domain accuracy claim."]}


def audit_molecular_evidence(run: dict, artifact_root: Path | str | None = None, *,
                             artifact_paths: dict[str, Path | str] | None = None) -> dict:
    """Audit accepted monomer prediction evidence with no network or writes.

    ``artifact_root`` is the runtime directory. Exported files may instead be
    provided in ``artifact_paths``, keyed by their accepted SHA256. No file path
    from a prompt, hypothesis, evidence text or model response is used directly.
    """
    if not isinstance(run, dict):
        raise TypeError("run must be a dictionary")
    artifact_paths = artifact_paths or {}
    result = {"schema_version": SCHEMA, "run_id": run.get("id"), "status": "no_molecular_evidence",
              "sequence_inventory": [], "comparisons": [], "limitations": list(COMMON_LIMITS),
              "method_sources": [
                  {"title": "NVIDIA Boltz2 NIM outputs", "url": "https://docs.nvidia.com/nim/bionemo/boltz2/1.8.0/inference.html",
                   "scope": "Confidence, pLDDT and optional PAE are distinct output types; deployed model version is not inferred from these docs."},
                  {"title": "ModelCIF quality-metric semantics", "url": "https://mmcif.wwpdb.org/dictionaries/mmcif_ma.dic/Items/_ma_qa_metric.type.html",
                   "scope": "Explicit metric type controls meaning; generic pLDDT and normalized pLDDT have different defined ranges."}]}
    evidence = {e.get("id"): e for e in run.get("evidence", []) if isinstance(e, dict)}
    for operation in run.get("followup_operations", [])[:100]:
        if not isinstance(operation, dict) or operation.get("kind") != "bionemo_public_structure":
            continue
        record = evidence.get(operation.get("evidence_id"))
        if not record:
            continue
        values = record.get("values", {})
        if not isinstance(values, dict):
            continue
        comparison = {"evidence_id": record["id"], "operation_id": operation.get("id"),
                      "status": "unavailable", "predictions": [], "settings_comparison": {"status": "unavailable"},
                      "alignment_sensitivity": {"status": "unavailable"}, "what_this_adds": [],
                      "limitations": list(values.get("limitations", []))}
        result["comparisons"].append(comparison)
        try:
            if operation.get("result_status") != "completed" or record.get("kind") != "prediction" or record.get("source", {}).get("sha256") != _hash(values):
                raise ValueError("The accepted prediction evidence hash/status does not verify")
            expected = values.get("predictions", [])
            if not isinstance(expected, list) or not 1 <= len(expected) <= 12 or any(not isinstance(p, dict) for p in expected):
                raise ValueError("Prediction inventory is absent or exceeds the bound")
            artifacts = operation.get("artifacts", [])
            if not isinstance(artifacts, list) or any(not isinstance(a, dict) for a in artifacts):
                raise ValueError("Invalid published artifact inventory")
            if sorted(a.get("sha256", "") for a in artifacts) != sorted(values.get("artifact_hashes", [])):
                raise ValueError("Published artifact inventory does not match accepted evidence")
            parsed = []
            for prediction in expected:
                item = {"label": prediction.get("label"), "request_id": prediction.get("request_id"),
                        "status": "unavailable", "sequence_ids": [], "confidence": {"status": "unavailable"},
                        "request_audit": {"status": "unavailable", "settings": {}}}
                comparison["predictions"].append(item)
                try:
                    if prediction.get("status") != "completed" or prediction.get("model") != "mit/boltz2":
                        raise ValueError("Only completed Boltz2 receipts are supported")
                    matches = [a for a in artifacts if a.get("label") == prediction.get("label") and a.get("request_id") == prediction.get("request_id")]
                    if len(matches) != 1:
                        raise ValueError("No unique matching artifact/receipt")
                    artifact = matches[0]
                    item["artifact_sha256"] = artifact["sha256"]
                    path, data = _artifact_path(run.get("id"), artifact, artifact_root, artifact_paths)
                    cif, chains = _parse(data)
                    if len(chains) != 1:
                        raise ValueError("This audit currently requires an isolated monomer receipt")
                    chain_id, chain = next(iter(chains.items()))
                    sequence = chain["sequence"]
                    checksum = _hash(sequence.encode())
                    if checksum != prediction.get("sequence_sha256") or len(sequence) != prediction.get("sequence_length"):
                        raise ValueError("Artifact sequence differs from the accepted provider receipt")
                    identifier = "sequence-" + checksum[:20]
                    role = "target" if values.get("scope") == "exploratory_public_isoform_structure" else "unassigned"
                    inventory = {"id": identifier, "role": role, "label": prediction.get("label"), "chain_id": chain_id,
                                 "sequence": sequence, "sequence_sha256": checksum, "length": len(sequence), "verified": True,
                                 "evidence_id": record["id"], "artifact_sha256": artifact["sha256"], "request_id": prediction.get("request_id"),
                                 "provenance": {"scope": values.get("scope"), "sources": values.get("input_sources", []),
                                                "mapping": values.get("mapping", {}), "identity_basis": "SHA256-matched accepted mmCIF plus exact sequence hash and length in the completed provider receipt"},
                                 "target_retention_established": False}
                    result["sequence_inventory"].append(inventory)
                    item.update(status="verified", model=prediction["model"], sequence_ids=[identifier],
                                global_provider_confidence=prediction.get("confidence_score"),
                                confidence=_confidence(cif, chain_id, sequence),
                                request_audit=_request_audit(path, prediction, artifact, chains))
                    parsed.append({"label": prediction.get("label"), "chains": chains})
                except (OSError, ValueError, KeyError, TypeError, PDBConstructionException) as exc:
                    item["reason"] = str(exc) if not isinstance(exc, OSError) else "Artifact file is unavailable"
            if all(p["status"] == "verified" for p in comparison["predictions"]):
                comparison["status"] = "verified_artifacts"
                comparison["what_this_adds"].append("Exact input sequences and saved coordinate identities verified independently of the prior narrative.")
                comparison["alignment_sensitivity"] = _alignment(values, parsed, comparison["predictions"])
            else:
                comparison["status"] = "partial"
            requests = [p["request_audit"] for p in comparison["predictions"]]
            if requests and all(r["status"] == "verified" for r in requests):
                equal = len({r["nonsequence_settings_sha256"] for r in requests}) == 1
                comparison["settings_comparison"] = {"status": "matched_submitted_settings" if equal else "different_submitted_settings",
                    "matched": equal, "comparison_basis": "All saved request fields except polymer sequence; MSA/template contents included in settings hash",
                    "limitations": ["Matching submitted settings does not establish a matching undisclosed server version, effective defaults or random seed."]}
                comparison["what_this_adds"].append("Saved submitted settings checked; unrecorded backend details remain explicit.")
            if comparison["alignment_sensitivity"].get("status") == "computed":
                comparison["what_this_adds"].append("Alignment sensitivity and any available local metric fields can now be reviewed without another NVIDIA call.")
        except (ValueError, TypeError, KeyError) as exc:
            comparison["reason"] = str(exc)
    if result["comparisons"]:
        result["status"] = "completed" if all(c["status"] == "verified_artifacts" for c in result["comparisons"]) else "partial"
    result["audit_sha256"] = _hash(result)
    return result
