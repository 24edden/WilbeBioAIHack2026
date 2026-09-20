"""Copy an existing authorized installed plugin subset into private app runtime."""
from pathlib import Path
import argparse
import hashlib
import json
import shutil

ROOT = Path(__file__).resolve().parents[1]

def install(source, destination=None):
    source = Path(source).resolve()
    target = Path(destination or ROOT / 'runtime/life-sciences-databases').resolve()
    manifest = json.loads((ROOT / 'skills/external-runtime-manifest.json').read_text())
    verified = []
    for relative, expected in manifest['files'].items():
        path = (source / relative).resolve()
        output = (target / relative).resolve()
        if not path.is_relative_to(source) or not output.is_relative_to(target) or not path.is_file():
            raise ValueError('Installed plugin subset is missing or outside its root')
        if hashlib.sha256(path.read_bytes()).hexdigest() != expected:
            raise ValueError('Installed plugin differs from the pinned version: ' + relative)
        verified.append((path, output))
    for path, output in verified:
        output.parent.mkdir(parents=True, exist_ok=True)
        if path != output:
            shutil.copyfile(path, output)
    return {'plugin':manifest['plugin'], 'version':manifest['version'], 'verified_files':len(verified)}

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('installed_plugin', type=Path)
    parser.add_argument('--destination', type=Path)
    args = parser.parse_args()
    print(json.dumps(install(args.installed_plugin, args.destination)))
