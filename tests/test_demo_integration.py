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
    assert "microscopy" not in twin.snapshot_at("T4").provenance
    assert twin.snapshot_at("T5").state["mri:lumbar_spine:bone_density:g_cm3"] == 1.28
