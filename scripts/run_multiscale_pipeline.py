from __future__ import annotations

import argparse
import json
from pathlib import Path

from backend.multiscale_pipeline import build_multiscale_run


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the multiscale evidence pipeline stages 26-34.")
    parser.add_argument("--root", default="data/raw")
    parser.add_argument("--subject", default=None)
    parser.add_argument("--timepoint", default="T0")
    parser.add_argument("--output", default="data/longitudinal/multiscale_run.json")
    args = parser.parse_args()
    payload = build_multiscale_run(args.root, args.subject, args.timepoint)
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    print(json.dumps({"pipeline_version": payload["pipeline_version"], "subject_id": payload["subject_id"], "timepoint": payload["timepoint"], "evidence_records": len(payload["evidence"]), "explicit_fusion_groups": len(payload["fusion"]["linked_groups"]), "unlinked_records": len(payload["fusion"]["rejected_unlinked_records"]), "output": str(output)}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
