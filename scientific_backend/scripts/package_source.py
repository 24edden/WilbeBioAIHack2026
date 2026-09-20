"""Portable source bundle; excludes private configuration, runtime and platform metadata."""
import argparse
import json
from pathlib import Path
import tarfile
import zipfile

ROOT = Path(__file__).resolve().parents[1]
def source_files():
    # Only reviewed public paths: hydration cannot silently add raw inputs,
    # installed plugins, credentials, databases or future private files.
    index = ROOT / "PUBLIC-SOURCE-FILES.json"
    for relative in json.loads(index.read_text())["files"]:
        path = ROOT / relative
        if (path.is_symlink() or any(parent.is_symlink() for parent in path.parents if parent.is_relative_to(ROOT) and parent != ROOT)
                or not path.resolve().is_relative_to(ROOT.resolve()) or not path.is_file()):
            raise ValueError("Public source file is missing or unsafe: " + relative)
        yield path, Path(relative)
    yield index, index.relative_to(ROOT)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    if args.output.suffix == ".zip":
        with zipfile.ZipFile(args.output, "w", zipfile.ZIP_DEFLATED) as bundle:
            for path, relative in source_files():
                if path.resolve() != args.output.resolve():
                    bundle.write(path, "team-tbd/" + relative.as_posix())
    else:
        with tarfile.open(args.output, "w:gz", format=tarfile.PAX_FORMAT) as bundle:
            for path, relative in source_files():
                if path.resolve() != args.output.resolve():
                    bundle.add(path, arcname=relative.as_posix(), recursive=False)
    print(str(args.output.resolve()))


if __name__ == "__main__":
    main()
