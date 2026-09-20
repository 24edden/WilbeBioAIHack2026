import argparse
import asyncio
import json
from pathlib import Path

from eval.investigation import InvestigationAdapter
from eval.runner import compare


def main():
    parser = argparse.ArgumentParser(description="Compare backend configurations on frozen cases")
    parser.add_argument("--manifest", type=Path, default=Path("eval/cases.json"))
    parser.add_argument("--configurations", type=Path, default=Path("eval/mock-configurations.json"))
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--concurrency", type=int, default=2)
    parser.add_argument("--repeats", type=int, default=1)
    parser.add_argument("--timeout", type=float, default=120)
    parser.add_argument("--live", action="store_true", help="Allow live configurations and billable provider calls")
    args = parser.parse_args()
    manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
    configs = json.loads(args.configurations.read_text(encoding="utf-8"))
    root = (args.manifest.parent / manifest.get("data_root", "..")).resolve()
    rows = asyncio.run(compare(manifest["cases"], configs,
        lambda: InvestigationAdapter(root, args.live), concurrency=args.concurrency,
        repeats=args.repeats, timeout_seconds=args.timeout, output=args.output))
    print(json.dumps({"trials": len(rows), "behavioral_passes": sum(row["behavioral_pass"] for row in rows),
                      "failures": sum(row["status"] != "complete" for row in rows),
                      "output": str(args.output), "scientific_correctness": "not assessed"}, indent=2))


if __name__ == "__main__":
    main()
