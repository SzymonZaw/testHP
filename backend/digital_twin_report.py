from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class DigitalTwinReport:
    subject_id: str
    hand_id: str
    timepoint_id: str
    anatomy: tuple[dict[str, Any], ...]
    tissues: tuple[dict[str, Any], ...]
    cells: tuple[dict[str, Any], ...]
    assessments: tuple[dict[str, Any], ...]
    biological_age: tuple[dict[str, Any], ...]
    trends: tuple[dict[str, Any], ...]
    attention: tuple[dict[str, Any], ...]
    spatial_attention: tuple[dict[str, Any], ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "subject_id": self.subject_id,
            "hand_id": self.hand_id,
            "timepoint_id": self.timepoint_id,
            "anatomy": list(self.anatomy),
            "tissues": list(self.tissues),
            "cells": list(self.cells),
            "assessments": list(self.assessments),
            "biological_age": list(self.biological_age),
            "trends": list(self.trends),
            "attention": list(self.attention),
            "spatial_attention": list(self.spatial_attention),
        }


def build_digital_twin_report(
    *,
    subject_id: str,
    hand_id: str,
    timepoint_id: str,
    anatomy: list[dict[str, Any]],
    tissues: list[dict[str, Any]],
    cells: list[dict[str, Any]],
    assessments: list[dict[str, Any]],
    biological_age: list[dict[str, Any]],
    trends: list[dict[str, Any]],
    attention: list[dict[str, Any]],
    spatial_attention: list[dict[str, Any]],
) -> dict[str, Any]:
    """Assemble one evidence-preserving snapshot of the hand digital twin."""
    groups = (anatomy, tissues, cells, assessments, biological_age, trends, attention, spatial_attention)
    for group in groups:
        for item in group:
            if not isinstance(item, dict):
                raise TypeError("report components must be dictionaries")
    return DigitalTwinReport(
        subject_id=subject_id,
        hand_id=hand_id,
        timepoint_id=timepoint_id,
        anatomy=tuple(anatomy),
        tissues=tuple(tissues),
        cells=tuple(cells),
        assessments=tuple(assessments),
        biological_age=tuple(biological_age),
        trends=tuple(trends),
        attention=tuple(attention),
        spatial_attention=tuple(spatial_attention),
    ).to_dict()
