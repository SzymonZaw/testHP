"""Command-line interface for testHP framework."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from .pipeline import FrameworkRunner


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="testhp",
        description="Operate and validate the testHP multimodal research pipeline.",
    )
    parser.add_argument("--root", default=".", help="Repository root (default: current directory).")
    sub = parser.add_subparsers(dest="command")

    sub.add_parser("status", help="Show datasets discovered under data/raw.")
    sub.add_parser("doctor", help="Check data availability and core Python imports.")
    run = sub.add_parser("run", help="Run the safe end-to-end framework smoke test.")
    run.add_argument("--no-report", action="store_true", help="Do not write a JSON run report.")
    sub.add_parser("help", help="Show this help message.")
    return parser


def _print_status(runner: FrameworkRunner) -> int:
    statuses, totals = runner.inspect_data()
    print("\ntestHP data status\n")
    print(f"Datasets: {totals['datasets']} | Ready: {totals['ready']} | Files: {totals['files']}")
    print("Modalities: " + (", ".join(totals["modalities"]) or "none"))
    print()
    for item in statuses:
        state = "READY" if item.ready else ("EMPTY" if item.exists else "MISSING")
        print(f"[{state:7}] {item.modality:7} {item.name:30} {item.files:8} files  {item.path}")
    return 0


def _print_doctor(runner: FrameworkRunner) -> int:
    statuses, totals = runner.inspect_data()
    imports = runner.check_imports()
    print("\ntestHP doctor\n")
    print(f"Raw data: {totals['ready']}/{totals['datasets']} datasets ready")
    print("Imports:")
    for module, state in imports.items():
        print(f"  {'✓' if state == 'ok' else '✗'} {module}: {state}")
    missing = [s for s in statuses if s.enabled and not s.ready]
    if missing:
        print("\nNote: unavailable datasets do not block the framework.")
    return 0 if all(state == "ok" for state in imports.values()) else 1


def _run(runner: FrameworkRunner, write_report: bool) -> int:
    print("\nRunning testHP framework smoke test...\n")
    result = runner.run_smoke()
    print(json.dumps(result.to_dict(), indent=2))
    if write_report:
        report = runner.write_report(result)
        print(f"\nReport: {report}")
    return 0 if result.twin_smoke.get("passed") else 1


def main(argv: list[str] | None = None) -> int:
    parser = _parser()
    args = parser.parse_args(argv)
    runner = FrameworkRunner(Path(args.root))
    if args.command in (None, "help"):
        parser.print_help()
        return 0
    if args.command == "status":
        return _print_status(runner)
    if args.command == "doctor":
        return _print_doctor(runner)
    if args.command == "run":
        return _run(runner, not args.no_report)
    parser.error(f"Unknown command: {args.command}")
    return 2
