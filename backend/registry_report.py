from __future__ import annotations

from dataclasses import asdict
from typing import Any, Iterable

from .attention_map import build_attention_map
from .digital_twin_report import build_digital_twin_report
from .longitudinal import compare_observations
from .longitudinal_observation import LongitudinalObservation
from .multiscale_registry import MultiscaleRegistry
from .spatial_attention import build_spatial_attention_map


def build_registry_report(
    registry: MultiscaleRegistry,
    *,
    subject_id: str,
    hand_id: str,
    timepoint_id: str,
    longitudinal_observations: Iterable[LongitudinalObservation] | None = None,
) -> dict[str, Any]:
    """Build a report using registry records and canonical cell read models."""
    registry.validate_integrity()

    def context(item: Any) -> bool:
        return (
            getattr(item, "subject_id", None) == subject_id
            and getattr(item, "hand_id", None) == hand_id
            and getattr(item, "timepoint_id", None) == timepoint_id
        )

    anatomy = [asdict(x) for x in registry.anatomy.values() if context(x)]
    tissues = [asdict(x) for x in registry.tissues.values() if context(x)]

    current_cells = [x for x in registry.cells.values() if context(x)]
    canonical_cells = [registry.canonical_cell_state(x.cell_id).to_dict() for x in current_cells]
    cells = [x["cell"] for x in canonical_cells]
    assessments = [x["state"] for x in canonical_cells]
    ages = [
        x["age_estimate"] for x in canonical_cells
        if x["age_estimate"] is not None
    ]

    typed = list(longitudinal_observations or ())
    for observation in typed:
        observation.validate()
        if observation.subject_id != subject_id or observation.hand_id != hand_id:
            raise ValueError("longitudinal observation context does not match report")

    observations = [observation.to_dict() for observation in typed]
    trends = compare_observations(subject_id, observations) if observations else []
    attention = build_attention_map([
        {
            "zone_id": x["zone"],
            "level": "cell",
            "metric": x["metric"],
            "cell_count": 1,
            "changed_cells": 1 if x.get("status") == "observed_change" else 0,
            "mean_delta": x.get("delta"),
        }
        for x in trends
        if x.get("status") != "insufficient_timepoints"
    ])

    cell_positions = {
        x.cell_id: {
            "x": float(x.position.get("x", 0.0)),
            "y": float(x.position.get("y", 0.0)),
            "z": float(x.position.get("z", 0.0)),
        }
        for x in current_cells
    }
    spatial = build_spatial_attention_map(
        attention,
        cell_positions=cell_positions,
        zone_cells={x["zone_id"]: (x["zone_id"],) for x in attention if x["level"] == "cell"},
    )

    return build_digital_twin_report(
        subject_id=subject_id,
        hand_id=hand_id,
        timepoint_id=timepoint_id,
        anatomy=anatomy,
        tissues=tissues,
        cells=cells,
        assessments=assessments,
        biological_age=ages,
        trends=trends,
        attention=attention,
        spatial_attention=spatial,
    )
