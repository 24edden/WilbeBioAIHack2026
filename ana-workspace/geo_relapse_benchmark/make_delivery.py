"""Build a checksummed, single-cohort instance delivery using only stdlib."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json
import tarfile
import sys

PACKAGE = Path(__file__).resolve().parent
ROOT = PACKAGE.parent
archive = Path(sys.argv[1]) if len(sys.argv) > 1 else Path('/tmp/GSE28460_clean_20260920.tar')
excluded = {'delivery_manifest.json', 'remote_delivery_verification.json',
            'instance_install_receipt.json'}
files = [ROOT / name for name in ['hypothesis.txt', 'AGENT_DATASET_README.txt',
                                  'START_HERE_GEO_RELAPSE.md']]
for directory in [PACKAGE, ROOT / 'datasets/agent_access/GSE28460']:
    files.extend(path for path in directory.rglob('*')
                 if path.is_file() and not path.is_symlink()
                 and path.name not in excluded and '__pycache__' not in path.parts)
files = sorted(set(files))
records = [{'path': str(path.relative_to(ROOT)), 'bytes': path.stat().st_size,
            'sha256': hashlib.sha256(path.read_bytes()).hexdigest()} for path in files]
manifest = {'created_at_utc': datetime.now(timezone.utc).isoformat(),
            'dataset': 'GSE28460', 'patients': 49, 'samples': 98, 'files': records}
manifest_path = PACKAGE / 'delivery_manifest.json'
manifest_path.write_text(json.dumps(manifest, indent=2) + '\n')
with tarfile.open(archive, 'w') as bundle:
    for path in files + [manifest_path]:
        bundle.add(path, arcname=str(path.relative_to(ROOT)), recursive=False)
print(json.dumps({'archive': str(archive), 'bytes': archive.stat().st_size,
                  'files': len(records), 'sha256': hashlib.sha256(archive.read_bytes()).hexdigest()}, indent=2))
