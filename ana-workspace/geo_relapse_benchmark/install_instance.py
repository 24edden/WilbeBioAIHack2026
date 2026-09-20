"""Install the verified single-cohort package and remove named superseded inputs.

Usage: python3 install_instance.py /home/ubuntu/GSE28460_clean_20260920.tar
This deliberately targets the team's agreed /home/ubuntu/ana-workspace directory.
It never removes historical analysis outputs or other project checkouts.
"""
from pathlib import Path, PurePosixPath
from datetime import datetime, timezone
import json
import shutil
import subprocess
import sys
import tarfile
import tempfile

ROOT = Path('/home/ubuntu/ana-workspace')
archive = Path(sys.argv[1]).resolve()
if archive != Path('/home/ubuntu/GSE28460_clean_20260920.tar'):
    raise ValueError('Expected the explicitly named GSE28460 delivery archive')
ROOT.mkdir(parents=True, exist_ok=True)
removed = []


def remove_exact(path):
    if not path.exists() and not path.is_symlink():
        return
    if path.is_symlink():
        size = 0
        path.unlink()
    elif path.is_dir():
        size = sum(p.stat().st_size for p in path.rglob('*')
                   if p.is_file() and not p.is_symlink())
        shutil.rmtree(path)
    else:
        size = path.stat().st_size
        path.unlink()
    removed.append({'path': str(path), 'bytes': size})


with tempfile.TemporaryDirectory(prefix='gse28460-staging-', dir=ROOT.parent) as tmp:
    staging = Path(tmp)
    with tarfile.open(archive) as bundle:
        for member in bundle.getmembers():
            name = PurePosixPath(member.name)
            if name.is_absolute() or '..' in name.parts or not member.isfile():
                raise ValueError(f'Unexpected archive member: {member.name}')
            target = staging.joinpath(*name.parts)
            target.parent.mkdir(parents=True, exist_ok=True)
            with bundle.extractfile(member) as source, target.open('wb') as dest:
                shutil.copyfileobj(source, dest)
    manifest_path = staging / 'geo_relapse_benchmark/delivery_manifest.json'
    manifest = json.loads(manifest_path.read_text())
    expected = {item['path'] for item in manifest['files']}
    actual = {str(p.relative_to(staging)) for p in staging.rglob('*') if p.is_file()}
    if actual != expected | {'geo_relapse_benchmark/delivery_manifest.json'}:
        raise ValueError('Archive contents do not match the delivery manifest')
    subprocess.run([sys.executable, str(staging / 'geo_relapse_benchmark/verify_delivery.py'),
                    str(staging)], check=True)
    for source in sorted(staging.rglob('*')):
        if source.is_file():
            destination = ROOT / source.relative_to(staging)
            destination.parent.mkdir(parents=True, exist_ok=True)
            if destination.is_symlink():
                raise ValueError(f'Refusing unexpected destination symlink: {destination}')
            shutil.copy2(source, destination)
    subprocess.run([sys.executable, str(ROOT / 'geo_relapse_benchmark/verify_delivery.py'),
                    str(ROOT)], check=True)

# Only obsolete input paths previously inventoried and authorized for deletion.
for relative in [
    'datasets/agent_access/cd19_tumour_pairs',
    'datasets/agent_access/paired_all_relapse',
    'archive/cd19_car_t_previous',
    'geo_relapse_benchmark/source/GSE18497_series_matrix.txt.gz',
    'geo_relapse_benchmark/source/GSE18497_sample_manifest.csv',
    'geo_relapse_benchmark/evaluator/discovery_B_ALL_arithmetic_reference.csv',
    'geo_relapse_benchmark/evaluator/validation_B_ALL_arithmetic_reference.csv',
    'geo_relapse_benchmark/evaluator/optional_T_ALL_arithmetic_reference.csv',
    'hypothesis/CD19_CAR_T_.txt',
    'hypothesis/BCMA_CAR_T_.txt',
    'datasets/provenance/DATASET_PROVENANCE.txt',
    'datasets/car_t_download.log',
    'datasets/car_t_redownload.log',
]:
    remove_exact(ROOT / relative)
remove_exact(Path('/home/ubuntu/geo_relapse_benchmark_20260920.tar'))
remove_exact(ROOT / 'input')
(ROOT / 'input').symlink_to('datasets/agent_access/GSE28460', target_is_directory=True)
(ROOT / 'hypothesis').mkdir(exist_ok=True)
remove_exact(ROOT / 'hypothesis/hypothesis.txt')
(ROOT / 'hypothesis/hypothesis.txt').symlink_to('../hypothesis.txt')
(ROOT / 'datasets/agent_access/README.txt').write_text(
    'One active patient dataset: GSE28460; 49 B-ALL patients, 98 paired samples.\n'
    'Start at /home/ubuntu/ana-workspace/hypothesis.txt and input/TASK.md.\n')
if (ROOT / 'input/hypothesis.txt').read_bytes() != (ROOT / 'hypothesis.txt').read_bytes():
    raise ValueError('Hypothesis copies disagree')
subprocess.run([sys.executable, str(ROOT / 'geo_relapse_benchmark/verify_delivery.py'),
                str(ROOT)], check=True)
cohorts = sorted(p.name for p in (ROOT / 'datasets/agent_access').iterdir() if p.is_dir())
if cohorts != ['GSE28460']:
    raise ValueError(f'Unexpected additional active dataset: {cohorts}')
remove_exact(archive)
receipt = {
    'completed_at_utc': datetime.now(timezone.utc).isoformat(),
    'instance': 'agentic-takeoff-cpu', 'root': str(ROOT),
    'active_dataset': 'GSE28460', 'patients': 49, 'samples': 98, 'probes': 54675,
    'input': str(ROOT / 'input'), 'input_resolves_to': str((ROOT / 'input').resolve()),
    'hypothesis': str(ROOT / 'hypothesis.txt'), 'hypothesis_copies_match': True,
    'active_dataset_directories': cohorts, 'removed': removed,
    'removed_bytes': sum(item['bytes'] for item in removed),
    'historical_analysis_outputs_preserved': True,
}
(ROOT / 'geo_relapse_benchmark/evaluator/instance_install_receipt.json').write_text(
    json.dumps(receipt, indent=2) + '\n')
print(json.dumps(receipt, indent=2))
