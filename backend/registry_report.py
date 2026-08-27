from __future__ import annotations

from dataclasses import asdict
from typing import Any, Iterable

from .attention_map import build_attention_map
from .cell_trajectory_aggregation import aggregate_cell_trajectories
from .digital_twin_report import build_digital_twin_report
from .longitudinal import compare_observations
from .longitudinal_cells import CellTimepointRecord, build_cell_trajectory
from .multiscale_registry import MultiscaleRegistry
from .spatial_attention import build_spatial_attention_map


def _dict_value(value: Any) -> dict[str, Any]:
    if isinstance(value, dict):
        return value
    if hasattr(value, "to_dict"):
        result = value.to_dict()
        if isinstance(result, dict):
            return result
    if hasattr(value, "__dataclass_fields__"):
        return asdict(value)
    raise TypeError("report component cannot be serialized as a dictionary")


def _age_report_value(value: Any) -> dict[str, Any]:
    data = _dict_value(value)
    if "biological_age_years" not in data and "estimated_age_years" in data:
        data = dict(data)
        data["biological_age_years"] = data["estimated_age_years"]
    return data


def _trajectory_records(observations: Iterable[Any]) -> list[CellTimepointRecord]:
    records: list[CellTimepointRecord] = []
    for item in observations:
        if isinstance(item, CellTimepointRecord):
            records.append(item)
    return records


def build_registry_report(
    registry: MultiscaleRegistry,
    *,
    subject_id: str,
    hand_id: str,
    timepoint_id: str,
    longitudinal_observations: Iterable[Any] | None = None,
) -> dict[str, Any]:
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
    cells = [_dict_value(x["cell"]) for x in canonical_cells]
    assessments = [
        _dict_value(x["state_assessment"])
        for x in canonical_cells
        if x["state_assessment"] is not None
    ]
    ages = [
        _age_report_value(x["age_estimate"])
        for x in canonical_cells
        if x["age_estimate"] is not None
    ]

    raw_observations = list(longitudinal_observations or ())
    observations: list[dict[str, Any]] = []
    for item in raw_observations:
        if hasattr(item, "validate"):
            item.validate()
            data = item.to_dict()
            if data.get("subject_id") != subject_id or data.get("hand_id") != hand_id:
                raise ValueError("longitudinal observation context does not match report")
            data.setdefault("zone", data.get("zone_id"))
            data.setdefault("timepoint", data.get("timepoint_id"))
        elif isinstance(item, dict):
            data = dict(item)
            if data.get("subject_id", subject_id) != subject_id or data.get("hand_id", hand_id) != hand_id:
                raise ValueError("longitudinal observation context does not match report")
        else:
            raise TypeError("longitudinal observations must be typed observations or dictionaries")
        observations.append(data)

    trends = compare_observations(subject_id, observations) if observations else []

    trajectory_groups: dict[str, list[CellTimepointRecord]] = {}
    for record in _trajectory_records(raw_observations):
        trajectory_groups.setdefault(record.cell_id, []).append(record)
    trajectories = [build_cell_trajectory(records) for records in trajectory_groups.values() if records]

    cell_to_tissue = {x.cell_id: x.tissue_id for x in current_cells}
    tissue_to_anatomy = {
        x.tissue_id: x.anatomical_structure_id
        for x in registry.tissues.values()
        if context(x)
    }
    multiscale_trends = (
        aggregate_cell_trajectories(
            trajectories,
            cell_to_tissue=cell_to_tissue,
            tissue_to_anatomy=tissue_to_anatomy,
        )
        if trajectories
        else []
    )
    trends = trends + [item.to_dict() for item in multiscale_trends]

    # The attention layer consumes every evidence-backed trend level. Spatial
    # projection remains intentionally cell-only because tissue/anatomy zones
    # do not yet have canonical 3D geometry in this report contract.
    attention_inputs = [
        {
            "zone_id": x.get("zone", x.get("zone_id")),
            "level": x.get("level", "cell"),
            "metric": x["metric"],
            "cell_count": x.get("cell_count", 1),
            "changed_cells": x.get("changed_cells", 1 if x.get("status") == "observed_change" else 0),
            "mean_delta": x.get("mean_delta", x.get("delta")),
        }
        for x in trends
        if x.get("status") != "insufficient_timepoints"
    ]
    attention = build_attention_map(attention_inputs)

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
        zone_cells={
            x["zone_id"]: (x["zone_id"],)
            for x in attention
            if x["level"] == "cell"
        },
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
