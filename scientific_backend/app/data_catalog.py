"""Read-only CAR-T dataset registry and bounded file-aware CPU analysis tools.

Model inputs select opaque file IDs, never filesystem paths. Source files remain
read-only. Full matrices are never densified; sparse gene summaries scan chunks.
"""
from __future__ import annotations
from collections import Counter
from contextlib import contextmanager
import copy
import csv
import gzip
import hashlib
import io
import json
import math
import os
from pathlib import Path, PurePosixPath
import tarfile
import time

from .cases import CASE_ROOT, SourceIntegrityError

REGISTRY_PATH = CASE_ROOT / "sources/brev-cart-catalog.json"
VERSION = "cart-file-analysis-1"
MAX_VERIFY_BYTES = 10 * 1024**3
MAX_MEMBER_BYTES = 512 * 1024**2
MAX_EXPANDED_BYTES = 768 * 1024**2
MAX_ROWS = 100_000
MAX_NNZ = 80_000_000
MAX_FEATURES = 150_000
MAX_CELLS = 300_000
MAX_SECONDS = 100
_HASH_CACHE = {}


class CatalogAnalysisError(ValueError):
    pass


def _canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)


def _sha(value):
    return hashlib.sha256(value if isinstance(value, bytes) else value.encode()).hexdigest()


def _registry():
    if REGISTRY_PATH.stat().st_size > 2_000_000:
        raise CatalogAnalysisError("Registry exceeds its metadata bound")
    data = json.loads(REGISTRY_PATH.read_text())
    if len(data["files"]) > 5000 or len({f["id"] for f in data["files"]}) != len(data["files"]):
        raise CatalogAnalysisError("Registry IDs are not unique or exceed the supported bound")
    from .gse28460_analysis import source_manifest, GEO_URL
    sources = source_manifest()
    data["datasets"].append({"id": "GSE28460", "title": "Paired B-ALL diagnosis/relapse — conventional treatment",
        "files_count": len(sources), "bytes": sum(s["bytes"] for s in sources),
        "description": "Ana agent-access input: 49 children, 98 paired Affymetrix arrays. Conventional ALL treatment, not CAR-T. Dedicated gse28460-paired-expression recipe preserves patient pairing and cohort scope.",
        "design": "Within-patient diagnosis versus relapse; all patients relapsed; no non-relapsing control. Prepared log2 microarray expression, not RNA-seq or surface antigen measurements."})
    data["files"].extend({"id": "ana-gse28460-" + source["name"].replace(".", "-"), "dataset_id": "GSE28460",
        "name": source["name"], "root": "ana_pairs", "relative_path": source["name"], "bytes": source["bytes"],
        "sha256": source["sha256"], "source_url": GEO_URL, "dedicated_analysis": "gse28460-paired-expression"} for source in sources)
    return data


def _record(file_id):
    if not isinstance(file_id, str):
        raise CatalogAnalysisError("A registered file ID is required")
    found = next((f for f in _registry()["files"] if f["id"] == file_id), None)
    if not found:
        raise CatalogAnalysisError("Unknown file ID; discover files through get_dataset first")
    return found


def _format(name):
    name = name.lower()
    if name.endswith((".tar", ".tar.gz", ".tgz")): return "archive"
    if name.endswith((".h5", ".hdf5", ".h5ad")): return "hdf5"
    if name.endswith((".mtx", ".mtx.gz")): return "matrix_market"
    if name.endswith((".rds", ".rds.gz")): return "rds"
    if name.endswith((".csv", ".csv.gz", ".tsv", ".tsv.gz", ".tab", ".tab.gz", ".txt", ".txt.gz", ".soft.gz")): return "table"
    if name.endswith(".json"): return "json"
    return "unsupported"


def _roots():
    return {"shared": Path(os.getenv("TEAM_TBD_DATA_ROOT", "/home/ubuntu/rosalind-shared-files")),
            "leon": Path(os.getenv("TEAM_TBD_LEON_ROOT", "/home/ubuntu/leon-workspace/bcma-gse164551-2026-09-19/input")),
            "ana": Path(os.getenv("TEAM_TBD_HYPOTHESIS_ROOT", "/home/ubuntu/ana-workspace/hypothesis")),
            "ana_pairs": Path(os.getenv("TEAM_TBD_GSE28460_ROOT", "/home/ubuntu/ana-workspace/datasets/agent_access/GSE28460"))}


def _path(record):
    root = _roots().get(record["root"])
    relative = PurePosixPath(record["relative_path"])
    if root is None or relative.is_absolute() or ".." in relative.parts:
        raise CatalogAnalysisError("Invalid registry path/root")
    root = root.resolve()
    path = (root / str(relative)).resolve()
    if not path.is_relative_to(root):
        raise CatalogAnalysisError("Registry path escapes its configured root")
    if path.is_file():
        return path
    # Exact previously hydrated public inputs can also run on the local demo.
    if not record.get("member"):
        candidates = {"GSE182891_CD19_minigene_variants.tab.gz": "cd19/GSE182891_CD19_minigene_variants.tab.gz",
                      "GSE182892_CD19_minigene_isoforms.txt.gz": "cd19/GSE182892_CD19_minigene_isoforms.txt.gz",
                      "CD19_CAR_T_.txt": "cd19/CD19_CAR_T_.txt"}
        if record["root"] == "leon" and record["name"] in ("case.json", "sample_manifest.tsv", "post_second_infusion_variants.tsv"):
            candidates[record["name"]] = "bcma/" + record["name"]
        fallback = candidates.get(record["name"])
        if fallback:
            return CASE_ROOT / "sources" / fallback
    return path


def _stat(path):
    s = path.stat()
    return (s.st_dev, s.st_ino, s.st_size, s.st_mtime_ns, s.st_ctime_ns)


def _verify_base(record):
    path = _path(record)
    if not path.is_file():
        raise CatalogAnalysisError("Registered data is not available on this host; set TEAM_TBD_DATA_ROOT on Brev. No synthetic replacement was used.")
    expected = record.get("parent_sha256") if record.get("member") else record.get("sha256")
    if not expected or len(expected) != 64:
        raise CatalogAnalysisError("No expected source hash is registered; analysis remains blocked")
    signature = _stat(path)
    if signature[2] > MAX_VERIFY_BYTES:
        raise CatalogAnalysisError("Selected source requires hashing more than the per-action limit; inspect catalog metadata or select a smaller qualified source")
    if not record.get("member") and signature[2] != record["bytes"]:
        raise SourceIntegrityError("Selected file size differs from the pinned registry")
    # Network/overlay filesystems can retain every stat field after an in-place
    # same-size rewrite. Stat signatures are not proof of immutable source bytes.
    # Always hash the selected enclosing file; only member digests can be reused
    # after that enclosing file's expected digest has just been reverified.
    digest = hashlib.sha256()
    start = time.monotonic()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(8 * 1024**2), b""):
            digest.update(chunk)
            if time.monotonic() - start > MAX_SECONDS:
                raise CatalogAnalysisError("Source verification exceeded its time bound; no analysis was accepted")
    if signature != _stat(path) or digest.hexdigest() != expected:
        raise SourceIntegrityError("Selected file bytes differ from the pinned registry")
    return path, expected, signature


@contextmanager
def _binary(record):
    path, _, _ = _verify_base(record)
    if record.get("member"):
        member = PurePosixPath(record["member"])
        if member.is_absolute() or ".." in member.parts or record["bytes"] > MAX_MEMBER_BYTES:
            raise CatalogAnalysisError("Unsafe or oversized archive member; no extraction performed")
        with tarfile.open(path, "r:") as archive:
            item = archive.getmember(record["member"])
            if not item.isfile() or item.size != record["bytes"]:
                raise SourceIntegrityError("Registered archive member identity/size changed")
            with archive.extractfile(item) as handle:
                yield handle
    else:
        with path.open("rb") as handle:
            yield handle


def _reference(record):
    path, parent_hash, signature = _verify_base(record)
    checksum = parent_hash
    if record.get("member"):
        key = (str(path), signature, record["member"])
        checksum = _HASH_CACHE.get(key)
        if checksum is None:
            digest = hashlib.sha256()
            with _binary(record) as handle:
                for chunk in iter(lambda: handle.read(8 * 1024**2), b""):
                    digest.update(chunk)
            checksum = digest.hexdigest()
            if signature != _stat(path):
                raise SourceIntegrityError("Archive changed during member hashing")
            _HASH_CACHE[key] = checksum
    return {"file_id": record["id"], "name": record["name"], "url": record["source_url"], "sha256": checksum,
            "archive_sha256": parent_hash if record.get("member") else None,
            "locator": record["relative_path"] + ("!" + record["member"] if record.get("member") else ""),
            "dataset_id": record["dataset_id"], "verification": "sha256-verified"}


def _public_file(record):
    available = _path(record).is_file()
    fmt = _format(record["name"])
    kinds = {"table": ["table_profile", "gene_summary"], "hdf5": ["sparse_summary", "gene_summary"],
             "matrix_market": ["sparse_summary", "gene_summary"], "archive": ["sparse_summary", "gene_summary"], "json": ["table_profile"]}.get(fmt, [])
    return {"id": record["id"], "dataset_id": record["dataset_id"], "name": record["name"], "format": fmt,
            "bytes": record["bytes"], "sha256": record.get("sha256"), "archive_id": record.get("archive_id"),
            "available": available, "verification": "catalog-unverified", "analysis_kinds": [] if record.get("dedicated_analysis") else kinds,
            "dedicated_analysis": record.get("dedicated_analysis"),
            "note": "Archive member; enclosing archive hash is verified before analytics." if record.get("member") else "Metadata inventory is not analysis or content verification."}


def list_datasets():
    registry = _registry()
    return {"registry_version": registry["version"], "inventory_date": registry["inventory_date"],
            "selection_rule": registry["selection_rule"],
            "datasets": [{**{key: ds[key] for key in ("id", "title", "files_count", "bytes")},
                          "description": ds["description"][:600], "verification": "catalog-unverified"} for ds in registry["datasets"]]}


def get_dataset(dataset_id):
    registry = _registry()
    dataset = next((d for d in registry["datasets"] if d["id"] == dataset_id), None)
    if not dataset:
        raise CatalogAnalysisError("Unknown dataset ID")
    return {**copy.deepcopy(dataset), "files": [_public_file(f) for f in registry["files"] if f["dataset_id"] == dataset_id],
            "limitations": ["Study membership does not establish matched patients across files or cohorts.", "Mixed CAR-T/TCE studies require sample-level treatment qualification.", "Archive members and parent files overlap; file counts are not independent observations."]}


@contextmanager
def _text(record):
    with _binary(record) as binary:
        if record["name"].lower().endswith(".gz"):
            with gzip.GzipFile(fileobj=binary) as unpacked:
                with io.TextIOWrapper(unpacked, encoding="utf-8-sig") as text:
                    yield text
        else:
            with io.TextIOWrapper(binary, encoding="utf-8-sig") as text:
                yield text


def _bounded_lines(handle):
    count = 0
    start = time.monotonic()
    while True:
        line = handle.readline(2_000_001)
        if not line:
            return
        count += len(line)
        if len(line) > 2_000_000 or count > MAX_EXPANDED_BYTES or time.monotonic() - start > MAX_SECONDS:
            raise CatalogAnalysisError("Expanded data/time bound exceeded; no partial result was accepted")
        yield line


def _decode(value):
    return value.decode("utf-8") if isinstance(value, bytes) else str(value)


def _bounded_members(archive):
    members = []; expanded = 0; started = time.monotonic()
    for index, item in enumerate(archive):
        expanded += item.size
        if index >= 1000 or expanded > MAX_EXPANDED_BYTES or time.monotonic()-started > MAX_SECONDS:
            raise CatalogAnalysisError("Nested archive member/expanded/time bound exceeded")
        path = PurePosixPath(item.name)
        if path.is_absolute() or '..' in path.parts or item.issym() or item.islnk():
            raise CatalogAnalysisError("Nested archive includes an unsafe member")
        if item.isfile(): members.append(item)
    return members


def _h5_local(parent, name, *, dataset=False):
    import h5py
    if name not in parent or not isinstance(parent.get(name, getlink=True), h5py.HardLink):
        raise CatalogAnalysisError("Only local hard-linked HDF5 objects are supported")
    obj = parent[name]
    if dataset:
        if not isinstance(obj, h5py.Dataset) or obj.is_virtual or obj.external:
            raise CatalogAnalysisError("External or virtual HDF5 data is not supported")
    elif not isinstance(obj, h5py.Group):
        raise CatalogAnalysisError("Expected an HDF5 group")
    return obj


def inspect_data_file(file_id):
    record = _record(file_id)
    public = _public_file(record)
    if not public["available"]:
        return {**public, "status": "unavailable", "reason": "Registered source is not mounted on this host."}
    if _format(record["name"]) == "rds":
        return {**public, "status": "adapter_required", "reason": "Large Seurat/RDS object requires an R-compatible sparse-object adapter; it is not loaded or densified here."}
    if not record.get("member") and record["bytes"] > MAX_VERIFY_BYTES:
        children = [_public_file(f) for f in _registry()["files"] if f.get("archive_id") == record["id"]]
        return {**public, "status": "catalog_only", "reason": "Enclosing file exceeds automatic verification bound; listed members are metadata, not verified measurements.", "members": children}
    ref = _reference(record)
    fmt = _format(record["name"])
    result = {**public, "status": "inspected", "verification": "sha256-verified", "source": ref}
    if fmt in ("table", "json"):
        with _text(record) as handle:
            lines = []
            for line in _bounded_lines(handle):
                lines.append(line.rstrip("\n")[:6000])
                if len(lines) == 5: break
        result["preview_lines"] = lines
        result["delimiter_hint"] = "tab" if lines and "\t" in lines[0] else "comma" if lines and "," in lines[0] else "unstructured"
        result["preview_is_not_full_analysis"] = True
    elif fmt == "matrix_market":
        with _text(record) as handle:
            for line in _bounded_lines(handle):
                if line.strip() and not line.startswith("%"):
                    result["shape_and_nnz"] = [int(x) for x in line.split()]
                    break
        result["companion_files"] = [_public_file(f) for f in _matrix_companions(record)]
    elif fmt == "hdf5":
        import h5py
        with _binary(record) as handle, h5py.File(handle, "r") as data:
            schema = []
            def visit(name, item):
                if len(schema) < 60 and isinstance(item, h5py.Dataset):
                    schema.append({"name": name, "shape": list(item.shape), "dtype": str(item.dtype)})
            # visititems does not follow soft/external links; terminate traversal
            # once the bounded schema preview is full.
            def bounded_visit(name, item):
                visit(name, item)
                return True if len(schema) >= 60 else None
            data.visititems(bounded_visit)
            result["schema"] = schema
            result["supported_layout"] = "Potential 10x CSC matrix; analysis validates local arrays" if isinstance(data.get("matrix", getlink=True), h5py.HardLink) else "Schema inspected; targeted adapter required"
    elif fmt == "archive":
        if record["name"].endswith(".tar") and not record.get("member"):
            result["members"] = [_public_file(f) for f in _registry()["files"] if f.get("archive_id") == record["id"]]
        else:
            with _binary(record) as handle, tarfile.open(fileobj=handle, mode="r:gz") as archive:
                members = [{"name": item.name, "bytes": item.size} for item in _bounded_members(archive)]
                result["members"] = members
                result["analysis_note"] = "A nested bundle with one matrix/features/barcodes triplet can be summarized using this same registered file ID."
    else:
        result.update(status="adapter_required", reason="No analytical reader is registered for this format.")
    return result


def _parameters(kind, parameters):
    p = copy.deepcopy({} if parameters is None else parameters)
    if not isinstance(p, dict): raise CatalogAnalysisError("Analysis parameters must be an object")
    allowed = {"table_profile": {"max_rows", "selected_columns"}, "gene_summary": {"genes", "feature_type"}, "sparse_summary": set()}
    if kind not in allowed or set(p) - allowed[kind]: raise CatalogAnalysisError("Unknown analysis kind or parameter")
    if kind == "table_profile":
        n = p.get("max_rows", 10000)
        if type(n) is not int or not 1 <= n <= MAX_ROWS: raise CatalogAnalysisError("max_rows must be between 1 and 100000")
        p["max_rows"] = n
        cols = p.get("selected_columns", [])
        if not isinstance(cols, list) or len(cols) > 20 or any(not isinstance(x, str) or len(x) > 200 for x in cols): raise CatalogAnalysisError("At most 20 named columns may be profiled")
    if kind == "gene_summary":
        genes = p.get("genes")
        if not isinstance(genes, list) or not 1 <= len(genes) <= 20 or any(not isinstance(g, str) or not g.strip() or len(g) > 100 for g in genes): raise CatalogAnalysisError("Supply 1–20 exact gene symbols or feature IDs")
        p["genes"] = list(dict.fromkeys(genes))
        if "feature_type" in p and (not isinstance(p["feature_type"], str) or not p["feature_type"].strip() or len(p["feature_type"]) > 100): raise CatalogAnalysisError("Invalid feature_type")
    return p


def _table_profile(record, p):
    if _format(record["name"]) == "json":
        with _text(record) as handle: value = json.loads("".join(_bounded_lines(handle)))
        return {"layout": "json", "keys": list(value)[:60] if isinstance(value, dict) else None, "records": len(value) if isinstance(value, (list, dict)) else 1, "preview": str(value)[:2000], "complete": True}
    with _text(record) as handle:
        lines = iter(_bounded_lines(handle))
        first = next(lines, "")
        delimiter = "\t" if "\t" in first else ","
        header = next(csv.reader([first], delimiter=delimiter)) if first else []
        if len(header) > 100_000: raise CatalogAnalysisError("Table column bound exceeded")
        selected = p.get("selected_columns") or header[:20]
        if any(c not in header for c in selected): raise CatalogAnalysisError("Selected column is absent from this source header")
        stats = {c: {"nonmissing": 0, "missing": 0, "numeric": 0, "nonfinite": 0, "sum": 0.0, "min": None, "max": None} for c in selected}
        indices = {c: header.index(c) for c in selected}
        rows = 0; malformed = 0; preview = []; complete = True
        for row in csv.reader(lines, delimiter=delimiter):
            if rows >= p["max_rows"]: complete = False; break
            rows += 1
            if len(row) != len(header): malformed += 1; continue
            if len(preview) < 3: preview.append({c: row[indices[c]][:200] for c in selected[:8]})
            for col, index in indices.items():
                val = row[index]; out = stats[col]
                if val.strip().lower() in ("", "na", "nan", "null", "none", "."):
                    out["missing"] += 1; continue
                out["nonmissing"] += 1
                try: number = float(val)
                except ValueError: continue
                if not math.isfinite(number): out["nonfinite"] += 1; continue
                out["numeric"] += 1; out["sum"] += number
                out["min"] = number if out["min"] is None else min(out["min"], number)
                out["max"] = number if out["max"] is None else max(out["max"], number)
        for value in stats.values(): value["mean_of_numeric_values"] = value["sum"] / value["numeric"] if value["numeric"] else None
        return {"layout": "delimited_table", "column_count": len(header), "columns": header[:100], "rows_profiled": rows, "malformed_rows": malformed, "complete": complete, "column_summaries": stats, "preview": preview, "sampling": "Source-order prefix; not a random sample"}


def _gene_table(record, p):
    requested = set(p["genes"]); found = []; scanned = 0
    with _text(record) as handle:
        lines = iter(_bounded_lines(handle)); first = next(lines, "")
        delim = "\t" if "\t" in first else ","; reader = csv.reader(lines, delimiter=delim)
        header = next(csv.reader([first], delimiter=delim))
        for row in reader:
            scanned += 1
            if scanned > MAX_ROWS: raise CatalogAnalysisError("Dense table row bound exceeded")
            if not row or row[0] not in requested: continue
            if len(row) not in (len(header), len(header) + 1) or len(row) - 1 > MAX_CELLS: raise CatalogAnalysisError("Gene-by-observation layout is not qualified")
            vals = []
            for cell in row[1:]:
                try: value = float(cell)
                except ValueError: raise CatalogAnalysisError("Selected gene row contains nonnumeric values; choose a qualified gene-by-observation matrix")
                if not math.isfinite(value): raise CatalogAnalysisError("Selected gene row contains missing/nonfinite values")
                vals.append(value)
            found.append({"gene": row[0], "observations": len(vals), "sum": sum(vals), "mean": sum(vals)/len(vals) if vals else None, "nonzero_observations": sum(x != 0 for x in vals), "source_line": scanned+1})
    return {"layout": "gene_by_observation_table", "rows_scanned": scanned, "genes": found, "missing_genes": sorted(requested - {r["gene"] for r in found}), "complete": True, "units": "Source numeric units; normalization and cell identity are not inferred"}


def _matrix_companions(record):
    name = record["name"]; suffix = "matrix.mtx.gz" if name.endswith("matrix.mtx.gz") else "matrix.mtx"
    if not name.endswith(suffix): return []
    prefix = name[:-len(suffix)]
    matches = []
    for other in _registry()["files"]:
        if other["dataset_id"] != record["dataset_id"] or other["root"] != record["root"]: continue
        if bool(other.get("member")) != bool(record.get("member")): continue
        if record.get("member") and other["relative_path"] != record["relative_path"]: continue
        if not record.get("member") and PurePosixPath(other["relative_path"]).parent != PurePosixPath(record["relative_path"]).parent: continue
        if other["name"] in [prefix+x for x in ("features.tsv.gz", "features.tsv", "genes.tsv.gz", "genes.tsv", "barcodes.tsv.gz", "barcodes.tsv")]: matches.append(other)
    return matches


def _read_features(handle, genes, feature_type):
    matches = {}; count = 0
    for line in _bounded_lines(handle):
        count += 1
        if count > MAX_FEATURES: raise CatalogAnalysisError("Feature count bound exceeded")
        fields = line.rstrip("\n").split("\t")
        if len(fields) < 3 and feature_type != "Gene Expression":
            raise CatalogAnalysisError("Legacy feature annotations do not qualify the requested modality; only the conventional Gene Expression default is supported")
        if feature_type and len(fields) > 2 and fields[2] != feature_type: continue
        for gene in genes:
            if gene in fields[:2]: matches.setdefault(count, []).append(gene)
    return count, matches


def _mtx_compute(matrix, features, genes, feature_type):
    import numpy as np
    count, selected = _read_features(features, genes, feature_type) if features else (None, {})
    lines = iter(_bounded_lines(matrix))
    banner = next(lines, "")
    if not banner.lower().startswith("%%matrixmarket matrix coordinate") or "general" not in banner.lower(): raise CatalogAnalysisError("Only general coordinate Matrix Market matrices are supported")
    dimensions = next((line for line in lines if line.strip() and not line.startswith("%")), "")
    try: nrows, ncols, nnz = map(int, dimensions.split())
    except ValueError: raise CatalogAnalysisError("Invalid Matrix Market dimensions")
    if min(nrows, ncols, nnz) < 0 or nrows > MAX_FEATURES or ncols > MAX_CELLS or nnz > MAX_NNZ: raise CatalogAnalysisError("Sparse matrix exceeds bounded dimensions/nonzeros")
    if count is not None and count != nrows: raise CatalogAnalysisError("Feature rows do not match matrix dimensions")
    vectors = {gene: np.zeros(ncols, dtype=float) for gene in genes}
    total = 0.0; seen = 0
    for line in lines:
        if not line.strip() or line.startswith("%"): continue
        parts = line.split()
        if len(parts) != 3: raise CatalogAnalysisError("Malformed coordinate row")
        row, col = int(parts[0]), int(parts[1]); value = float(parts[2])
        if not 1 <= row <= nrows or not 1 <= col <= ncols or not math.isfinite(value) or value < 0: raise CatalogAnalysisError("Invalid coordinate or count")
        seen += 1
        if seen > nnz: raise CatalogAnalysisError("More coordinate rows than declared")
        total += value
        for gene in selected.get(row, []): vectors[gene][col-1] += value
    if seen != nnz: raise CatalogAnalysisError("Coordinate count differs from declared nonzero entries")
    matched = {g for value in selected.values() for g in value}
    output = [{"gene": gene, "feature_rows": [row for row, labels in selected.items() if gene in labels], "sum": float(vectors[gene].sum()), "mean_per_barcode": float(vectors[gene].mean()) if ncols else None, "nonzero_barcodes": int(np.count_nonzero(vectors[gene]))} for gene in genes if gene in matched]
    return {"layout": "matrix_market_coordinate", "features": nrows, "barcodes": ncols, "stored_entries": seen, "total_counts": total, "genes": output, "missing_genes": [g for g in genes if g not in matched], "feature_type": feature_type, "complete": True, "dense_matrix_allocated": False}


def _mtx_analysis(record, p):
    companions = _matrix_companions(record)
    feature = next((f for f in companions if "features.tsv" in f["name"] or "genes.tsv" in f["name"]), None)
    genes = p.get("genes", [])
    if genes and feature is None: raise CatalogAnalysisError("Registered feature companion is required for gene identity")
    refs = [_reference(record)]
    with _text(record) as matrix:
        if feature:
            refs.append(_reference(feature))
            with _text(feature) as features: value = _mtx_compute(matrix, features, genes, p.get("feature_type", "Gene Expression"))
        else: value = _mtx_compute(matrix, None, genes, p.get("feature_type", "Gene Expression"))
    return value, refs


def _h5_analysis(record, p):
    import h5py
    import numpy as np
    with _binary(record) as handle, h5py.File(handle, "r") as data:
        if "matrix" not in data: raise CatalogAnalysisError("This HDF5 file is not a qualified 10x matrix; inspect schema and use a dedicated CNV/molecule adapter")
        group = _h5_local(data, "matrix")
        arrays = {key: _h5_local(group, key, dataset=True) for key in ("shape", "data", "indices", "indptr")}
        if arrays['shape'].shape != (2,) or arrays['shape'].dtype.kind not in 'iu' or any(arrays[k].ndim != 1 for k in ('data','indices','indptr')):
            raise CatalogAnalysisError("Invalid sparse array dimensions")
        if any(arrays[k].dtype.kind not in 'iu' for k in ('indices','indptr')) or arrays['data'].dtype.kind not in 'iuf':
            raise CatalogAnalysisError("Invalid sparse array dtypes")
        nrows, ncols = map(int, arrays["shape"][:]); nnz = arrays["data"].shape[0]
        if min(nrows, ncols) < 0 or nrows > MAX_FEATURES or ncols > MAX_CELLS or nnz > MAX_NNZ: raise CatalogAnalysisError("HDF5 sparse dimensions exceed limits")
        if group["indices"].shape != (nnz,) or group["indptr"].shape != (ncols+1,): raise CatalogAnalysisError("Invalid CSC matrix arrays")
        pointers = group["indptr"][:]
        if pointers[0] != 0 or pointers[-1] != nnz or np.any(np.diff(pointers.astype('int64')) < 0): raise CatalogAnalysisError("Invalid CSC column pointers")
        features = _h5_local(group, "features")
        annotations = {key: _h5_local(features, key, dataset=True) for key in ("name", "id")}
        if "feature_type" in features: annotations['feature_type'] = _h5_local(features, "feature_type", dataset=True)
        for arr in annotations.values():
            if arr.shape != (nrows,) or arr.dtype.kind not in 'SO' or (arr.dtype.kind == 'S' and arr.dtype.itemsize > 1000):
                raise CatalogAnalysisError("Feature annotation shape/type bound mismatch")
        def strings(arr):
            result = []
            for start in range(0, nrows, 1000):
                chunk = [_decode(v) for v in arr[start:start+1000]]
                if any(len(v) > 1000 for v in chunk): raise CatalogAnalysisError("Feature string length bound exceeded")
                result.extend(chunk)
            return result
        names = strings(annotations['name']); ids = strings(annotations['id'])
        types = strings(annotations['feature_type']) if 'feature_type' in annotations else ["Gene Expression"]*nrows
        genes = p.get("genes", []); selected = {}; feature_type = p.get("feature_type", "Gene Expression")
        for index, (name, ident, typ) in enumerate(zip(names, ids, types)):
            if typ == feature_type:
                for gene in genes:
                    if gene in (name, ident): selected.setdefault(index, []).append(gene)
        vectors = {g: np.zeros(ncols, dtype=float) for g in genes}; total = 0.0; started = time.monotonic()
        for start in range(0, nnz, 1_000_000):
            end = min(start+1_000_000, nnz); values = group["data"][start:end]; indices = group["indices"][start:end]
            if np.any(indices < 0) or np.any(indices >= nrows) or np.any(values < 0) or not np.isfinite(values).all(): raise CatalogAnalysisError("Sparse matrix contains invalid indices/counts")
            total += float(values.sum(dtype='float64'))
            if selected:
                mask = np.isin(indices, list(selected)); offsets = np.flatnonzero(mask)
                cols = np.searchsorted(pointers, start+offsets, side="right")-1
                for row, labels in selected.items():
                    chosen = indices[offsets] == row
                    for gene in labels: np.add.at(vectors[gene], cols[chosen], values[offsets[chosen]])
            if time.monotonic()-started > MAX_SECONDS: raise CatalogAnalysisError("Sparse HDF5 analysis exceeded time bound")
        matched = {g for labels in selected.values() for g in labels}
        output = [{"gene": g, "feature_rows": [i for i, labels in selected.items() if g in labels], "sum": float(vectors[g].sum()), "mean_per_barcode": float(vectors[g].mean()) if ncols else None, "nonzero_barcodes": int(np.count_nonzero(vectors[g]))} for g in genes if g in matched]
        return {"layout": "10x_hdf5_csc", "features": nrows, "barcodes": ncols, "stored_entries": nnz, "total_counts": total, "genes": output, "missing_genes": [g for g in genes if g not in matched], "feature_type": feature_type, "feature_types": dict(Counter(types)), "complete": True, "dense_matrix_allocated": False}


def _bundle_analysis(record, p):
    if not record["name"].endswith((".tar.gz", ".tgz")): raise CatalogAnalysisError("Select a registered matrix or nested matrix bundle inside the archive")
    if record["bytes"] > MAX_MEMBER_BYTES: raise CatalogAnalysisError("Nested bundle exceeds compressed size bound")
    with _binary(record) as binary, tarfile.open(fileobj=binary, mode="r:gz") as archive:
        members = _bounded_members(archive)
        matrices = [m for m in members if m.name.endswith(("matrix.mtx", "matrix.mtx.gz"))]
        if len(matrices) != 1: raise CatalogAnalysisError("Nested bundle must contain exactly one matrix triplet")
        matrix = matrices[0]; folder = str(PurePosixPath(matrix.name).parent)
        features = [m for m in members if str(PurePosixPath(m.name).parent)==folder and PurePosixPath(m.name).name in ("features.tsv", "features.tsv.gz", "genes.tsv", "genes.tsv.gz")]
        if len(features) != 1: raise CatalogAnalysisError("Nested matrix feature identity is ambiguous")
        @contextmanager
        def text_member(member):
            if member.size > MAX_EXPANDED_BYTES or member.name.startswith('/') or '..' in PurePosixPath(member.name).parts: raise CatalogAnalysisError("Nested member is unsafe or oversized")
            with archive.extractfile(member) as handle:
                if member.name.endswith('.gz'):
                    with gzip.GzipFile(fileobj=handle) as gz, io.TextIOWrapper(gz) as text: yield text
                else:
                    with io.TextIOWrapper(handle) as text: yield text
        # tarfile extract streams share seek position but tar ExFileObjects support independent seeks.
        with text_member(features[0]) as feats:
            feature_bytes = ''.join(_bounded_lines(feats))
        with text_member(matrix) as mat:
            value = _mtx_compute(mat, io.StringIO(feature_bytes), p.get('genes',[]), p.get('feature_type','Gene Expression'))
        value['nested_matrix_locator'] = matrix.name; value['nested_feature_locator'] = features[0].name
        return value


def analyze_data_file(file_id, analysis_kind, parameters=None):
    record = _record(file_id); p = _parameters(analysis_kind, parameters)
    fmt = _format(record["name"])
    refs = [_reference(record)]
    if analysis_kind == "table_profile" and fmt in ("table", "json"):
        result = _table_profile(record, p)
    elif analysis_kind in ("gene_summary", "sparse_summary") and fmt == "hdf5":
        result = _h5_analysis(record, p)
    elif analysis_kind in ("gene_summary", "sparse_summary") and fmt == "matrix_market":
        result, refs = _mtx_analysis(record, p)
    elif analysis_kind in ("gene_summary", "sparse_summary") and fmt == "archive":
        result = _bundle_analysis(record, p)
    elif analysis_kind == "gene_summary" and fmt == "table":
        result = _gene_table(record, p)
    else:
        raise CatalogAnalysisError("This file format does not support the selected analysis; inspect the file and choose a registered compatible source")
    # Detect any source mutation during analytics, even after a cached verification.
    for reference in refs:
        if _reference(_record(reference["file_id"])) != reference: raise SourceIntegrityError("Source version changed during analysis")
    values = {"analysis_id": "catalog:"+analysis_kind, "analysis_version": VERSION, "case_id": "cart-discovery", "dataset_id": record["dataset_id"], "file_id": file_id, "parameters": p, "input_sources": refs, "result": result,
              "limitations": ["Descriptive source-file analysis; barcodes are not independent patients.", "Sample identity, treatment, timepoints and malignant-cell annotation must be qualified before cross-file biological comparison.", "RNA expression does not establish accessible surface protein, CAR recognition, affinity or therapeutic efficacy.", "Counts from parent archives and extracted/prepared copies are not independent evidence."], "inference_performed": False}
    evidence_id = "DATA-"+_sha(_canonical({"file_id":file_id,"kind":analysis_kind,"parameters":p}))[:20]
    summary = f"Computed {analysis_kind} on {record['dataset_id']} / {record['name']}. "
    if "barcodes" in result: summary += f"Source matrix has {result['features']:,} features and {result['barcodes']:,} barcodes; {result['stored_entries']:,} sparse entries scanned without a dense matrix."
    elif "rows_profiled" in result: summary += f"Profiled {result['rows_profiled']:,} source-order rows; complete={result['complete']}; malformed rows={result['malformed_rows']}."
    else: summary += "Returned bounded source-linked values with explicit identity and interpretation limits."
    return {"id": evidence_id, "title": f"{record['dataset_id']} · {analysis_kind}", "kind": "derived", "summary": summary,
            "source": {"name": "Runtime catalog analysis", "url": record["source_url"], "locator": record["name"]+"; "+analysis_kind+"; canonical values JSON", "sha256": _sha(_canonical(values))}, "values": values}


def validate_catalog_evidence(evidence):
    values = evidence.get("values", {})
    if evidence.get("kind") != "derived" or values.get("case_id") != "cart-discovery" or values.get("analysis_version") != VERSION:
        raise CatalogAnalysisError("Invalid catalog evidence identity/version")
    kind = values.get("analysis_id", "").removeprefix("catalog:")
    parameters = _parameters(kind, values.get("parameters"))
    record = _record(values.get("file_id"))
    expected_id = "DATA-"+_sha(_canonical({"file_id":record['id'],"kind":kind,"parameters":parameters}))[:20]
    if evidence.get("id") != expected_id or values.get("dataset_id") != record["dataset_id"] or evidence.get("source", {}).get("sha256") != _sha(_canonical(values)):
        raise CatalogAnalysisError("Catalog result identity/hash differs from its source-linked recipe")
    sources = values.get("input_sources", [])
    if not sources or sources[0].get("file_id") != record["id"]:
        raise CatalogAnalysisError("Primary analyzed source is missing from evidence")
    allowed = {record["id"], *(r["id"] for r in _matrix_companions(record))}
    for reference in sources:
        if reference.get("file_id") not in allowed or reference != _reference(_record(reference["file_id"])):
            raise SourceIntegrityError("Catalog evidence source does not match its verified registry identity")


def discovery_case():
    registry = _registry(); data = REGISTRY_PATH.read_bytes(); checksum = _sha(data)
    text = (CASE_ROOT / "sources/cd19/CD19_CAR_T_.txt").read_text()
    total = sum(d["bytes"] for d in registry["datasets"])
    evidence = {"id":"CATALOG-CART-01", "title":"Brev CAR-T source inventory", "kind":"literature",
                "summary":f"Read-only inventory contains {len(registry['datasets'])} dataset groups and {len(registry['files'])} registered files/archive members, representing {total:,} top-level bytes. Inventory is not content validation or biological analysis.",
                "source":{"name":"brev-cart-catalog.json","url":"","locator":"Registry version "+registry['version']+"; datasets and files metadata","sha256":checksum},
                "values":{"datasets_count":len(registry['datasets']),"files_count":len(registry['files']),"bytes":total,"verification":"catalog-unverified","selection_rule":registry['selection_rule']}}
    return {"id":"cart-discovery", "title":"CAR-T discovery workspace", "subtitle":"Agent-selected studies and analyses across the Brev data library", "hypothesis":text,
            "hypothesis_source":{"name":"CD19_CAR_T_.txt","url":"","locator":"Original Brev hypothesis; user may replace with their own research question","sha256":_sha(text)},
            "description":"Discover real CAR-T and related antigen-escape studies, inspect source files, choose appropriate bounded analyses, and request evidence-driven review cycles.", "data_mode":"public_evidence", "evidence_count":1,"evidence":[evidence],
            "readiness":[{"label":"Shared registry","status":"ready","detail":f"{len(registry['datasets'])} dataset groups; {len(registry['files'])} files and archive members."},{"label":"Source verification","status":"limited","detail":"Hash verification runs when an actual file is selected; metadata listing is not validation."},{"label":"Dataset-specific analysis","status":"ready","detail":"Sparse HDF5/MTX and bounded tables; unsupported RDS/CNV formats stay explicit."}],
            "limitations":["Includes mixed CAR-T/TCE cohorts and parent metadata series; qualify sample-level treatment and overlap.","Large Seurat RDS, copy-number-specific HDF5 and unsupported formats need dedicated adapters; no whole-dataset clinical result is implied.","Model-led study/analysis selection is exploratory; no prospective mechanism accuracy or causal proof is claimed."],
            "source_integrity":{"status":"catalog-unverified","registry_sha256":checksum},
            "demo_decision":{"summary":"This workspace requires a live investigation to choose datasets and analyses.","assessment":"not_evaluable","claims":[],"alternatives":[],"limitations":["No live investigation was performed in demonstration mode."],"next_experiment":{"title":"Run a live source-qualified investigation","design":"Choose evidence and compute applicable analyses before specifying an experiment.","positive":"Evidence informs a discriminator.","negative":"Evidence challenges the supplied hypothesis.","inconclusive":"Appropriate inputs remain missing."},"rd_handoff":{"objective":text,"status":"blocked","reference":"No molecular construct qualified","candidates":[],"modeling":{"status":"blocked","reason":"Exact constructs and relevant target state are required.","artifacts":[]},"experiment_id":"","return_requirements":["Qualified evidence assessment and experiment design"]}}}
