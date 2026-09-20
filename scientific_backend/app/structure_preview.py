"""Bounded visual geometry from verified provider artifacts, never invented images."""
from __future__ import annotations

import hashlib
import io
import math
from Bio.PDB import MMCIFParser


def preview_from_cif(data: bytes, *, receipt: dict, scope: str, cif_url: str) -> dict:
    if not isinstance(data, bytes) or not 0 < len(data) <= 10_000_000:
        raise ValueError("Structure preview exceeds the artifact bound")
    checksum = hashlib.sha256(data).hexdigest()
    allowed = {item.get("sha256") for item in receipt.get("artifacts", []) if isinstance(item, dict)}
    if receipt.get("sha256"):
        allowed.add(receipt["sha256"])
    if checksum not in allowed:
        raise ValueError("Structure preview does not match its verified receipt")
    if not isinstance(cif_url, str) or not cif_url.startswith("/api/"):
        raise ValueError("Structure download must be a local registered artifact")
    structure = MMCIFParser(QUIET=True, auth_chains=False, auth_residues=False).get_structure(
        "verified", io.StringIO(data.decode("utf-8")))
    models = list(structure.get_models())
    if len(models) != 1:
        raise ValueError("Preview requires exactly one structural model")
    chains, count = [], 0
    for chain in models[0]:
        points = []
        for residue in chain:
            if "CA" not in residue:
                continue
            coordinates = [float(x) for x in residue["CA"].coord]
            if not all(math.isfinite(x) for x in coordinates):
                raise ValueError("Preview coordinates must be finite")
            count += 1
            if count > 12_000:
                raise ValueError("Preview exceeds the residue bound")
            points.append(dict(zip(("x", "y", "z"), [round(x, 4) for x in coordinates])) | {
                "residue_index": int(residue.id[1]), "residue_name": str(residue.resname)[:5]})
        if points:
            chains.append({"id": str(chain.id)[:8], "points": points})
    if not chains or len(chains) > 12:
        raise ValueError("No bounded protein backbone is available")
    public = {"model": str(receipt.get("model", "mit/boltz2"))[:80], "sha256": checksum}
    if receipt.get("request_id"):
        public["request_id"] = str(receipt["request_id"])[:200]
    score = receipt.get("confidence_score")
    if type(score) in (int, float) and math.isfinite(score) and 0 <= score <= 1:
        public["confidence_score"] = score
    return {"status": "completed", "scope": scope, "receipt": public, "chains": chains,
            "residue_count": count, "cif_url": cif_url,
            "representation": "Alpha-carbon trace from the actual returned NVIDIA coordinates",
            "limitations": ["Predicted coordinates are not experimental measurements.",
                            "This trace does not display glycans, binding affinity or cellular activity."]}
