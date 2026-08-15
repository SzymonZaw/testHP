from __future__ import annotations

import argparse
import json
from pathlib import Path

from backend.hand_vision import analyze_own_cohort, observations_from_analysis


def main() -> None:
    parser = argparse.ArgumentParser(description="Analyze own hand images with MediaPipe Hands.")
    parser.add_argument("--root", default="data/raw/hand/own_cohort")
    parser.add_argument("--subject", default="own_cohort")
    parser.add_argument("--session", default="session-001")
    parser.add_argument("--timepoint", default="T0")
    parser.add_argument("--output", default="data/longitudinal/own_hand_vision_T0.json")
    args = parser.parse_args()

    analysis = analyze_own_cohort(args.root)
    observations = observations_from_analysis(
        analysis,
        subject_id=args.subject,
        session_id=args.session,
        timepoint=args.timepoint,
    )
    payload = {
        **analysis,
        "observation_count": len(observations),
        "observations": observations,
        "subject_linking": {
            "explicit": True,
            "subject_id": args.subject,
            "note": "The CLI subject identifier is an explicit research label; it is not inferred from image similarity.",
        },
    }
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({
        "status": "ok" if analysis["files_analyzed"] else "warning",
        "files_found": analysis["files_found"],
        "files_analyzed": analysis["files_analyzed"],
        "files_failed": analysis["files_failed"],
        "observations": len(observations),
        "output": str(output),
    }, indent=2))


if __name__ == "__main__":
    main()
