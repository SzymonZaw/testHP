"""High-level orchestration for the testHP research prototype."""

from __future__ import annotations

from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
import importlib
import json
from typing import Any

from .data import DatasetStatus, discover_raw, summary


CORE_MODULES = (
    "core",
    "analysis",
    "integration.observation_to_twin",
    "organism.digital_twin",
    "validation",
    "audit",
)


@dataclass
class RunResult:
    started_at: str
    finished_at: str
    data: dict[str, Any]
    imports: dict[str, str]
    twin_smoke: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class FrameworkRunner:
    """Discover data and exercise the common observation-to-twin path.

    This is intentionally a safe research smoke runner. It does not invent
    biological measurements and it does not claim to execute unavailable model
    stages. Dataset-specific adapters can be added later without changing the
    CLI contract.
    """

    def __init__(self, repo_root: str | Path = ".") -> None:
        self.repo_root = Path(repo_root).resolve()

    def inspect_data(self) -> tuple[list[DatasetStatus], dict[str, Any]]:
        statuses = discover_raw(self.repo_root)
        return statuses, summary(statuses)

    def check_imports(self) -> dict[str, str]:
        result: dict[str, str] = {}
        for module in CORE_MODULES:
            try:
                importlib.import_module(module)
                result[module] = "ok"
            except Exception as exc:  # import errors are diagnostics, not crashes
                result[module] = f"error: {type(exc).__name__}: {exc}"
        return result

    def twin_smoke(self) -> dict[str, Any]:
        """Verify the existing observation -> digital-twin contract with fixtures."""
        from datetime import datetime
        from integration.observation_to_twin import Observation, ObservationToTwinPipeline
        from organism.digital_twin import DigitalBiologicalTwin

        twin = DigitalBiologicalTwin(subject_id="framework-smoke")
        pipeline = ObservationToTwinPipeline(twin, minimum_quality=0.5)
        snapshot = pipeline.ingest(
            "T0",
            [
                Observation("framework_fixture", 1.0, quality_score=1.0, modality="framework"),
                Observation("rejected_fixture", 99.0, quality_score=0.1, modality="framework"),
            ],
            datetime.now(timezone.utc),
        )
        return {
            "passed": snapshot.state == {"framework_fixture": 1.0},
            "accepted_features": sorted(snapshot.state),
            "provenance": list(snapshot.provenance),
            "snapshot_count": len(twin.snapshots),
        }

    def run_smoke(self) -> RunResult:
        started = datetime.now(timezone.utc)
        _, data_summary = self.inspect_data()
        imports = self.check_imports()
        twin = self.twin_smoke()
        finished = datetime.now(timezone.utc)
        return RunResult(
            started_at=started.isoformat(),
            finished_at=finished.isoformat(),
            data=data_summary,
            imports=imports,
            twin_smoke=twin,
        )

    def write_report(self, result: RunResult, output_dir: str | Path = "reports/framework") -> Path:
        target = self.repo_root / output_dir
        target.mkdir(parents=True, exist_ok=True)
        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        path = target / f"run_{stamp}.json"
        path.write_text(json.dumps(result.to_dict(), indent=2), encoding="utf-8")
        return path
