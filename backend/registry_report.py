from __future__ import annotations

from dataclasses import asdict
from typing import Any

from .digital_twin_report import build_digital_twin_report
from .multiscale_registry import MultiscaleRegistry


def build_registry_report(
    registry: MultiscaleRegistry,
    *,
    subject_id: str,
    hand_id: str,
    timepoint_id: str,
) -> dict[str, Any]:
    """Build a report directly from the registry's canonical in-memory records.

    Records are filtered by the requested subject/hand/timepoint. No synthetic
    anatomy, cell measurements, assessments, or spatial coordinates are added.
    The registry integrity is checked before producing the snapshot.
    """
    registry.validate_integrity()

    def context(item: Any) -> bool:
        return (
            getattr(item, "subject_id", None) == subject_id
            and getattr(item, "hand_id", None) == hand_id
            and getattr(item, "timepoint_id", None) == timepoint_id
        )

    anatomy = [asdict(x) for x in registry.anatomy.values() if context(x)]
    tissues = [asdict(x) for x in registry.tissues.values() if context(x)]
    cells = [asdict(x) for x in registry.cells.values() if context(x)]
    assessments = [asdict(x) for x in registry.biological_state_assessments.values() if context(x)]
    ages = [asdict(x) for x in registry.biological_age_estimates.values() if context(x)]

    return build_digital_twin_report(
        subject_id=subject_id,
        hand_id=hand_id,
        timepoint_id=timepoint_id,
        anatomy=anatomy,
        tissues=tissues,
        cells=cells,
        assessments=assessments,
        biological_age=ages,
        trends=[],
        attention=[],
        spatial_attention=[],
    )
