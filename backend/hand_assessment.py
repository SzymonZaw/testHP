"""Descriptive assessment assembled from longitudinal hand signals."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .change_relationship import ChangeRelationship
from .function_trajectory import FunctionTrajectory
from .hand_trajectory import HandTrajectory
from .health_trajectory import HealthTrajectory
from .region_trajectory import RegionTrajectory


@dataclass(frozen=True)
class HandAssessment:
    """Non-diagnostic summary of observed longitudinal changes."""

    overall_status: str
    ageing_signal: str
    health_signal: str
    function_signal: str
    relationship: str
    affected_regions: tuple[str, ...]
    evidence: dict[str, Any]

    @classmethod
    def from_trajectories(
        cls,
        hand: HandTrajectory,
        health: HealthTrajectory,
        function: FunctionTrajectory,
        relationship: ChangeRelationship,
        regions: tuple[RegionTrajectory, ...] = (),
    ) -> "HandAssessment":
        ageing_rate = hand.ageing_rate()
        ageing_signal = "insufficient_data"
        if ageing_rate is not None:
            ageing_signal = "accelerated_change" if ageing_rate > 1.0 else "stable_or_slow_change"

        health_magnitude = relationship.health_change_magnitude
        function_magnitude = relationship.function_change_magnitude
        health_signal = "insufficient_data" if not health.points else (
            "stable" if health_magnitude == 0 else "changing"
        )
        function_signal = "insufficient_data" if not function.points else (
            "stable" if function_magnitude == 0 else "changing"
        )

        if not hand.points or not health.points or not function.points:
            overall = "insufficient_data"
        elif health_signal == "stable" and function_signal == "stable":
            overall = "stable"
        else:
            overall = "observe"

        affected = tuple(
            sorted({trajectory.region_id for trajectory in regions if _region_changed(trajectory)})
        )
        latest_confidence = hand.points[-1].confidence if hand.points else 0.0
        evidence = {
            "age_delta": hand.age_delta,
            "ageing_rate": ageing_rate,
            "health_change_magnitude": health_magnitude,
            "function_change_magnitude": function_magnitude,
            "region_count": len(regions),
            "confidence": latest_confidence,
        }
        return cls(
            overall_status=overall,
            ageing_signal=ageing_signal,
            health_signal=health_signal,
            function_signal=function_signal,
            relationship=relationship.interpretation,
            affected_regions=affected,
            evidence=evidence,
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "overall_status": self.overall_status,
            "ageing_signal": self.ageing_signal,
            "health_signal": self.health_signal,
            "function_signal": self.function_signal,
            "relationship": self.relationship,
            "affected_regions": self.affected_regions,
            "evidence": self.evidence,
        }


def _region_changed(trajectory: RegionTrajectory) -> bool:
    return any(
        value not in (None, 0, 0.0)
        for value in (
            trajectory.age_delta,
            trajectory.cell_count_delta,
            trajectory.confidence_delta,
        )
    ) or _distribution_changed(trajectory)


def _distribution_changed(trajectory: RegionTrajectory) -> bool:
    if len(trajectory.points) < 2:
        return False
    first, last = trajectory.points[0], trajectory.points[-1]
    return first.health_distribution != last.health_distribution or first.function_distribution != last.function_distribution
