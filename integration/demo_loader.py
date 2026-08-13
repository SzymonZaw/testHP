"""Loader for the deterministic synthetic demo dataset."""

from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path

from integration.observation_to_twin import Observation


@dataclass(frozen=True)
class DemoRecord:
    subject_id: str
    timepoint: str
    anatomical_site: str
    unit: str
    observation: Observation


def load_demo(path: str | Path) -> list[DemoRecord]:
    """Load raw/demo/observations.csv without changing the source data."""
    records: list[DemoRecord] = []
    with Path(path).open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            records.append(
                DemoRecord(
                    subject_id=row["subject_id"],
                    timepoint=row["timepoint"],
                    anatomical_site=row["anatomical_site"],
                    unit=row["unit"],
                    observation=Observation(
                        feature=row["feature"],
                        value=float(row["value"]),
                        quality_score=float(row["quality_score"]),
                        modality=row["modality"],
                    ),
                )
            )
    return records
