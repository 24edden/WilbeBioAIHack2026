"""Verify every delivered checksum and reopen all matrices using only stdlib."""
from pathlib import Path
import csv
import gzip
import hashlib
import json
import math
import sys
from datetime import datetime, timezone

root = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).resolve().parent.parent
package = root / "geo_relapse_benchmark"
manifest = json.loads((package / "delivery_manifest.json").read_text())
for record in manifest["files"]:
    path = root / record["path"]
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    assert path.stat().st_size == record["bytes"] and digest.hexdigest() == record["sha256"], path

results = {}
for name, expected in [("discovery_B_ALL", 49), ("validation_B_ALL", 27), ("optional_T_ALL", 14)]:
    folder = root / "datasets/agent_access/paired_all_relapse" / name
    with (folder / "samples.csv").open() as handle:
        samples = list(csv.DictReader(handle))
    with (folder / "patient_pairs.csv").open() as handle:
        pairs = list(csv.DictReader(handle))
    assert len(pairs) == expected and len(samples) == expected * 2
    lookup = {sample["sample_id"]: sample for sample in samples}
    assert len(lookup) == len(samples)
    for pair in pairs:
        for time in ["diagnosis", "relapse"]:
            sample = lookup[pair[time]]
            assert sample["patient_id"] == pair["patient_id"] and sample["timepoint"] == time
    with gzip.open(folder / "expression_log2.tsv.gz", "rt") as handle:
        reader = csv.reader(handle, delimiter="\t")
        header = next(reader)
        assert header[1:] == [sample["sample_id"] for sample in samples]
        probes = set()
        for row in reader:
            assert len(row) == len(header) and row[0] not in probes
            assert all(math.isfinite(float(x)) for x in row[1:])
            probes.add(row[0])
    assert len(probes) == 54675
    results[name] = {"patients": len(pairs), "samples": len(samples), "probes": len(probes),
                     "matrix_opened": True, "pairs_verified": True}
report = {"verified_at_utc": datetime.now(timezone.utc).isoformat(), "root": str(root.resolve()),
          "files_checksum_verified": len(manifest["files"]), "groups": results}
(package / "evaluator/remote_delivery_verification.json").write_text(json.dumps(report, indent=2) + "\n")
print(json.dumps(report, indent=2))
