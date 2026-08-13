from datetime import datetime, timezone
from pathlib import Path

from integration.demo_loader import load_demo
from integration.observation_to_twin import ObservationToTwinPipeline
from organism.digital_twin import DigitalBiologicalTwin


def test_demo_loads_and_ingests_quality_filtered_observations():
    path = Path(__file__).parents[1] / "raw" / "demo" / "observations.csv"
    records = load_demo(path)
    assert len(records) == 25
    assert any(r.observation.quality_score < 0.5 for r in records)

    twin = DigitalBiologicalTwin(subject_id="DEMO-001")
    pipeline = ObservationToTwinPipeline(twin, minimum_quality=0.5)

    by_timepoint = {}
    for record in records:
        by_timepoint.setdefault(record.timepoint, []).append(record.observation)

    for index, timepoint in enumerate(sorted(by_timepoint)):
        pipeline.ingest(
            timepoint,
            by_timepoint[timepoint],
            datetime(2026, 1, 1 + index, tzinfo=timezone.utc),
        )

    assert len(twin.history()) == 6
    # T4 microscopy has quality 0.20 and must not enter the snapshot.
    assert "microscopy" not in twin.snapshot_at("T4").provenance
    assert all("microscopy" not in key for key in twin.snapshot_at("T4").state)
    # T5 deliberately contains two MRI measurements and both are retained.
    assert twin.snapshot_at("T5").state["bone_density"] == 1.05
    assert twin.snapshot_at("T5").state["bone_density_alt"] == 1.28
