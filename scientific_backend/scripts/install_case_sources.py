"""Hydrate ignored scientific inputs from explicit local/public sources, enforcing pins.

No model calls, provider probes, arbitrary archive extraction or source regeneration.
"""
from __future__ import annotations

import argparse
import csv
import gzip
import hashlib
import io
import json
from pathlib import Path
import tempfile
from urllib.request import urlopen

ROOT = Path(__file__).resolve().parents[1]
BCMA_FIELDS = ["Hugo_Symbol", "NCBI_Build", "Chromosome", "Start_Position", "End_Position",
               "Reference_Allele", "Tumor_Seq_Allele2", "Variant_Classification", "HGVSc",
               "HGVSp_Short", "Transcript_ID", "t_depth", "t_ref_count", "t_alt_count",
               "n_depth", "n_ref_count", "n_alt_count", "FILTER"]


def prepare_bcma(content: bytes, preparation: dict) -> bytes:
    """Reproduce only the already-pinned compact column projection, not analysis."""
    if (len(content) != preparation["bytes"]
            or hashlib.sha256(content).hexdigest() != preparation["sha256"]):
        raise ValueError("BCMA source changed; preserving original source pin")
    text = gzip.decompress(content).decode("utf-8")
    rows = list(csv.DictReader((line for line in text.splitlines() if not line.startswith("#")), delimiter="\t"))
    if (len(rows) != preparation["rows"] or any(set(BCMA_FIELDS + ["Tumor_Sample_Barcode"]) - row.keys() for row in rows)
            or {row["NCBI_Build"] for row in rows} != {"GRCh38"}
            or {row["Tumor_Sample_Barcode"] for row in rows} != {"CRB_401_MS7856"}):
        raise ValueError("BCMA source identity/schema differs from its preparation contract")
    output = io.StringIO(newline="")
    writer = csv.DictWriter(output, fieldnames=BCMA_FIELDS, delimiter="\t", lineterminator="\n", extrasaction="ignore")
    writer.writeheader()
    writer.writerows(rows)
    return output.getvalue().encode("utf-8")


def valid(path: Path, record: dict) -> bool:
    return (path.is_file() and path.stat().st_size == record["bytes"]
            and hashlib.sha256(path.read_bytes()).hexdigest() == record["sha256"])


def install(source: Path | None = None, *, download_public: bool = False, check: bool = False,
            root: Path = ROOT) -> dict:
    case_root = (root / "casepacks").resolve()
    records = json.loads((case_root / "MANIFEST.json").read_text())["source_files"]
    external = {item["path"]: item for item in
                json.loads((case_root / "EXTERNAL-INPUTS.json").read_text())["inputs"]}
    source = source.resolve() if source else None
    pending = []
    for record in records:
        target = (case_root / record["path"]).resolve()
        if not target.is_relative_to(case_root):
            raise ValueError("Input path escapes the case pack")
        if target.exists():
            if not valid(target, record):
                raise ValueError("Existing source differs from its pin; refusing overwrite: " + record["path"])
            continue
        if check:
            raise ValueError("Missing pinned input: " + record["path"])
        incoming = (source / record["path"]).resolve() if source else None
        if incoming and incoming.is_relative_to(source) and incoming.is_file():
            if not valid(incoming, record):
                raise ValueError("Supplied source differs from its pin: " + record["path"])
            content = incoming.read_bytes()
        elif download_public and external.get(record["path"], {}).get("url"):
            definition = external[record["path"]]
            url = definition["url"]
            if not url.startswith("https://"):
                raise ValueError("Public input URL must use HTTPS")
            with urlopen(url, timeout=60) as response:
                content = response.read(definition.get("preparation", record)["bytes"] + 1)
            if definition.get("preparation"):
                if definition["preparation"].get("kind") != "bcma-pinned-column-projection-v1":
                    raise ValueError("Unknown external source preparation")
                content = prepare_bcma(content, definition["preparation"])
            if len(content) != record["bytes"] or hashlib.sha256(content).hexdigest() != record["sha256"]:
                raise ValueError("Public source changed; preserving original pin: " + record["path"])
        else:
            raise ValueError("Supply --from-casepacks for missing pinned input: " + record["path"])
        pending.append((target, content))
    # Validate every input before publishing any installation writes.
    for target, content in pending:
        target.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile(dir=target.parent, delete=False) as handle:
            temporary = Path(handle.name)
            handle.write(content)
        try:
            # Link is atomic and refuses overwrite if another process created it.
            target.hardlink_to(temporary)
        finally:
            temporary.unlink(missing_ok=True)
    return {"status": "verified", "source_count": len(records), "installed": len(pending), "external_calls": 0 if not download_public else "public downloads only; no inference"}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--from-casepacks", type=Path, help="Existing authorized casepacks directory")
    parser.add_argument("--download-public", action="store_true", help="Explicitly download/prepare pinned public inputs without inference")
    parser.add_argument("--check", action="store_true", help="Verify existing bytes without reading sources or downloading")
    args = parser.parse_args()
    try:
        print(json.dumps(install(args.from_casepacks, download_public=args.download_public, check=args.check)))
    except (ValueError, OSError) as error:
        raise SystemExit(str(error)) from error
