"""Distribution/privacy and external-data installer checks; no model/network calls."""
import hashlib
import gzip
import importlib.util
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


def script(name):
    spec = importlib.util.spec_from_file_location(name, ROOT / "scripts" / (name + ".py"))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_source_bundle_has_explicit_public_inventory_and_excludes_hydrated_inputs():
    module = script("package_source")
    paths = {relative.as_posix() for _, relative in module.source_files()}
    assert {"app/providers.py", "app/worker.py", "skills/manifest.json", ".env.example"} <= paths
    assert not any(p.startswith(("runtime/", ".venv/")) or p == ".env" for p in paths)
    external = json.loads((ROOT / "casepacks/EXTERNAL-INPUTS.json").read_text())["inputs"]
    assert not {"casepacks/" + item["path"] for item in external} & paths
    assert not any(p.endswith((".sqlite", ".pyc", ".xlsx", ".gz")) for p in paths)


def test_all_public_scientific_skills_keep_their_exact_pinned_bytes():
    from app.scientific_skills import skill_catalog, load_skill
    for item in skill_catalog():
        if item.get("external_plugin"):
            continue
        for role in item["roles"]:
            loaded = load_skill(item["id"], role)
            assert hashlib.sha256(loaded["instructions"].encode()).hexdigest() == item["sha256"]


def test_source_bundle_rejects_a_symlinked_public_directory(tmp_path):
    module = script("package_source")
    (tmp_path / "runtime").mkdir()
    (tmp_path / "runtime/main.py").write_text("private runtime contents")
    (tmp_path / "app").symlink_to(tmp_path / "runtime", target_is_directory=True)
    (tmp_path / "PUBLIC-SOURCE-FILES.json").write_text(json.dumps({"files": ["app/main.py"]}))
    module.ROOT = tmp_path
    with pytest.raises(ValueError, match="unsafe"):
        list(module.source_files())


def inputs(tmp_path):
    root, supplied = tmp_path / "app", tmp_path / "source"
    (root / "casepacks").mkdir(parents=True)
    (supplied / "sources").mkdir(parents=True)
    records = [{"path": "sources/a.txt", "bytes": 1, "sha256": hashlib.sha256(b"a").hexdigest()},
               {"path": "sources/b.txt", "bytes": 1, "sha256": hashlib.sha256(b"b").hexdigest()}]
    (root / "casepacks/MANIFEST.json").write_text(json.dumps({"source_files": records}))
    (root / "casepacks/EXTERNAL-INPUTS.json").write_text(json.dumps({"inputs": records}))
    (supplied / "sources/a.txt").write_bytes(b"a")
    (supplied / "sources/b.txt").write_bytes(b"b")
    return root, supplied


def test_local_input_install_is_pinned_and_repeatable(tmp_path):
    root, supplied = inputs(tmp_path)
    module = script("install_case_sources")
    assert module.install(supplied, root=root)["installed"] == 2
    assert module.install(supplied, root=root)["installed"] == 0
    assert module.install(check=True, root=root)["source_count"] == 2


def test_invalid_input_does_not_publish_partial_install(tmp_path):
    root, supplied = inputs(tmp_path)
    (supplied / "sources/b.txt").write_bytes(b"bad")
    with pytest.raises(ValueError, match="differs from its pin"):
        script("install_case_sources").install(supplied, root=root)
    assert not (root / "casepacks/sources/a.txt").exists()


def test_existing_source_is_never_overwritten(tmp_path):
    root, supplied = inputs(tmp_path)
    (root / "casepacks/sources").mkdir()
    target = root / "casepacks/sources/a.txt"
    target.write_bytes(b"changed")
    with pytest.raises(ValueError, match="refusing overwrite"):
        script("install_case_sources").install(supplied, root=root)
    assert target.read_bytes() == b"changed"


def test_path_escape_is_rejected(tmp_path):
    root, supplied = inputs(tmp_path)
    manifest = root / "casepacks/MANIFEST.json"
    data = json.loads(manifest.read_text())
    data["source_files"][0]["path"] = "../outside.txt"
    manifest.write_text(json.dumps(data))
    with pytest.raises(ValueError, match="escapes"):
        script("install_case_sources").install(supplied, root=root)


def test_bcma_preparation_enforces_source_pin_identity_and_column_order():
    module = script("install_case_sources")
    columns = module.BCMA_FIELDS + ["Tumor_Sample_Barcode", "Unused_column"]
    values = {key: "value" for key in columns}
    values.update(NCBI_Build="GRCh38", Tumor_Sample_Barcode="CRB_401_MS7856")
    source = gzip.compress(("# Original public MAF metadata\n" + "\t".join(columns) + "\n"
                            + "\t".join(values[key] for key in columns) + "\n").encode(), mtime=0)
    preparation = {"bytes": len(source), "sha256": hashlib.sha256(source).hexdigest(), "rows": 1}
    result = module.prepare_bcma(source, preparation).decode()
    assert result.splitlines()[0] == "\t".join(module.BCMA_FIELDS)
    assert result.splitlines()[1] == "\t".join(values[key] for key in module.BCMA_FIELDS)
    assert "Unused_column" not in result
    with pytest.raises(ValueError, match="source changed"):
        module.prepare_bcma(source + b"changed", preparation)
    with pytest.raises(ValueError, match="identity/schema"):
        module.prepare_bcma(source, {**preparation, "rows": 2})
