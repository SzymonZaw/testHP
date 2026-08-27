from __future__ import annotations

"""PostgreSQL persistence for longitudinal tissue trajectories."""

from dataclasses import asdict
from typing import Any

from psycopg.types.json import Json

from .database import connect, ensure_schema
from .tissue_longitudinal import TissueTrajectory


def _json(value: Any) -> Json:
    return Json(asdict(value) if hasattr(value, "__dataclass_fields__") else value)


def register_tissue_trajectory(trajectory: TissueTrajectory) -> TissueTrajectory:
    """Persist a validated trajectory as one immutable-in-shape time series."""
    trajectory.validate()
    ensure_schema()
    with connect() as conn:
        conn.execute(
            """INSERT INTO tissue_trajectories
               (trajectory_id, tissue_id, subject_id, hand_id, points, provenance, uncertainty)
               VALUES (%s,%s,%s,%s,%s,%s,%s)
               ON CONFLICT (trajectory_id) DO UPDATE SET
                 tissue_id=EXCLUDED.tissue_id,
                 subject_id=EXCLUDED.subject_id,
                 hand_id=EXCLUDED.hand_id,
                 points=EXCLUDED.points,
                 provenance=EXCLUDED.provenance,
                 uncertainty=EXCLUDED.uncertainty""",
            (
                trajectory.trajectory_id,
                trajectory.tissue_id,
                trajectory.subject_id,
                trajectory.hand_id,
                _json([asdict(point) for point in trajectory.points]),
                _json(trajectory.provenance),
                _json(trajectory.uncertainty),
            ),
        )
    return trajectory


def load_tissue_trajectory(trajectory_id: str) -> dict[str, Any] | None:
    """Return the persisted trajectory payload for API/read-model consumers."""
    ensure_schema()
    with connect() as conn:
        row = conn.execute(
            "SELECT trajectory_id,tissue_id,subject_id,hand_id,points,provenance,uncertainty,created_at "
            "FROM tissue_trajectories WHERE trajectory_id=%s",
            (trajectory_id,),
        ).fetchone()
    return row
