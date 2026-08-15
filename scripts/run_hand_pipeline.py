from __future__ import annotations

import argparse
import json
from pathlib import Path

from backend.hand_pipeline import run_hand_pipeline


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the own-cohort hand stages 21-25 pipeline.")
    parser.add_argument("--root", default="data/raw/hand/own_cohort")
    parser.add_argument("--subject", required=True)
    parser.add_argument("--session", default="session-001")
    parser.add_argument("--timepoint", default="T0")
    parser.add_argument("--output", default="data/longitudinal/own_hand_pipeline_T0.json")
    args = parser.parse_args()

    payload = run_hand_pipeline(
        root=Path(args.root),
        subject_id=args.subject,
        session_id=args.session,
        timepoint_id=args.timepoint,
    )
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, ensure_ascii=False, indent=2, default=str), encoding="utf-8")

    summary = {
        "status": "ok" if payload["analysis"]["files_analyzed"] else "warning",
        "subject_id": args.subject,
        "timepoint": args.timepoint,
        "files_found": payload["analysis"]["files_found"],
        "files_analyzed": payload["analysis"]["files_analyzed"],
        "files_failed": payload["analysis"]["files_failed"],
        "measurements": len(payload["measurements"]),
        "usable_measurements": sum(1 for item in payload["quality"] if item["usable"]),
        "zones": sum(1 for item in payload["zone_map"].values() if item["measurements"]),
        "longitudinal_changes": len(payload["longitudinal_changes"]),
        "output": str(output),
    }
    print(json.dumps(summary, indent=2))
    if payload["analysis"].get("errors"):
        print("\nDetailed errors:")
        for error in payload["analysis"]["errors"]:
            print(f" - {error['source_file']} -> {error['error']}")


if __name__ == "__main__":
    main()
