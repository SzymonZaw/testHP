"""
Temporal state for longitudinal digital-twin tracking.

Stores T0, T1, T2, T3 and future timepoints, including regional trajectories.
"""

from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Any, Dict, List, Optional
from datetime import datetime


@dataclass
class TimePoint:
    """Represents one longitudinal observation."""

    name: str
    timestamp: Optional[str] = None
    biological_age: Optional[float] = None
    overall_risk: Optional[float] = None
    tissue_state: Dict[str, Any] = field(default_factory=dict)
    cell_state: Dict[str, Any] = field(default_factory=dict)
    region_state: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class TemporalState:
    """Stores the complete longitudinal trajectory."""

    timepoints: List[TimePoint] = field(default_factory=list)
    current_timepoint: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def add_timepoint(self, name: str, biological_age: Optional[float] = None, overall_risk: Optional[float] = None,
                      tissue_state: Optional[Dict[str, Any]] = None, cell_state: Optional[Dict[str, Any]] = None,
                      region_state: Optional[Dict[str, Dict[str, Any]]] = None, timestamp: Optional[str] = None,
                      metadata: Optional[Dict[str, Any]] = None) -> None:
        """Add or replace a longitudinal timepoint."""
        existing = self.get_timepoint(name)
        point = TimePoint(name=name, timestamp=timestamp or datetime.utcnow().isoformat(), biological_age=biological_age,
                          overall_risk=overall_risk, tissue_state=tissue_state or {}, cell_state=cell_state or {},
                          region_state=region_state or {}, metadata=metadata or {})
        if existing is not None:
            self.timepoints[self.timepoints.index(existing)] = point
        else:
            self.timepoints.append(point)
        self.current_timepoint = name

    def get_timepoint(self, name: str) -> Optional[TimePoint]:
        """Find a timepoint by name."""
        for point in self.timepoints:
            if point.name == name:
                return point
        return None

    def get_trajectory(self, attribute: str) -> List[Dict[str, Any]]:
        """Extract a longitudinal trajectory for a top-level attribute."""
        return [{"timepoint": point.name, "value": getattr(point, attribute, None), "timestamp": point.timestamp}
                for point in self.timepoints]

    def get_region_trajectory(self, region_id: str, attribute: str) -> List[Dict[str, Any]]:
        """Extract one region's measurements across all timepoints."""
        return [{"timepoint": point.name, "value": point.region_state.get(region_id, {}).get(attribute),
                 "timestamp": point.timestamp} for point in self.timepoints]

    def calculate_change(self, attribute: str) -> Optional[float]:
        """Calculate change between first and last valid top-level observations."""
        values = [getattr(point, attribute, None) for point in self.timepoints]
        values = [value for value in values if value is not None]
        if len(values) < 2:
            return None
        return float(values[-1] - values[0])

    def calculate_region_change(self, region_id: str, attribute: str) -> Optional[float]:
        """Calculate first-to-last change for one region."""
        values = [point.region_state.get(region_id, {}).get(attribute) for point in self.timepoints]
        values = [value for value in values if value is not None]
        if len(values) < 2:
            return None
        return float(values[-1] - values[0])

    def compare_regions(self, first: str, last: str) -> Dict[str, Dict[str, Any]]:
        """Compare two named timepoints region by region."""
        start = self.get_timepoint(first)
        end = self.get_timepoint(last)
        if start is None or end is None:
            raise ValueError("both timepoints must exist")
        region_ids = set(start.region_state) | set(end.region_state)
        result: Dict[str, Dict[str, Any]] = {}
        numeric_fields = ("biological_age", "abnormal_fraction", "unknown_fraction", "confidence", "heterogeneity")
        for region_id in sorted(region_ids):
            before, after = start.region_state.get(region_id, {}), end.region_state.get(region_id, {})
            deltas: Dict[str, float] = {}
            for field_name in numeric_fields:
                old, new = before.get(field_name), after.get(field_name)
                if isinstance(old, (int, float)) and isinstance(new, (int, float)):
                    deltas[field_name] = float(new - old)
            age_delta, abnormal_delta = deltas.get("biological_age"), deltas.get("abnormal_fraction")
            if age_delta is None and abnormal_delta is None:
                direction = "uncertain"
            elif (age_delta is not None and age_delta > 0) or (abnormal_delta is not None and abnormal_delta > 0):
                direction = "deteriorating"
            elif (age_delta is not None and age_delta < 0) or (abnormal_delta is not None and abnormal_delta < 0):
                direction = "improving"
            else:
                direction = "stable"
            result[region_id] = {"from": before, "to": after, "deltas": deltas, "direction": direction}
        return result

    def analyze_region_trend(self, region_id: str) -> Dict[str, Any]:
        """Classify a region's longitudinal trend without making a diagnosis."""
        observations = []
        for point in self.timepoints:
            region = point.region_state.get(region_id, {})
            age, abnormal = region.get("biological_age"), region.get("abnormal_fraction")
            if isinstance(age, (int, float)) or isinstance(abnormal, (int, float)):
                observations.append((point, age, abnormal))
        if len(observations) < 3:
            return {"region_id": region_id, "trend": "uncertain", "confidence": 0.0,
                    "observation_count": len(observations), "evidence": []}
        age_values = [float(age) for _, age, _ in observations if isinstance(age, (int, float))]
        abnormal_values = [float(value) for _, _, value in observations if isinstance(value, (int, float))]
        evidence: List[str] = []

        def direction(values: List[float]) -> Optional[str]:
            if len(values) < 3:
                return None
            first, last = values[1] - values[0], values[-1] - values[-2]
            if first > 0 and last > 0: return "up"
            if first < 0 and last < 0: return "down"
            if last == 0 and first == 0: return "flat"
            return "mixed"

        age_direction, abnormal_direction = direction(age_values), direction(abnormal_values)
        if age_direction == "up": evidence.append("biological_age_increasing")
        if abnormal_direction == "up": evidence.append("abnormal_fraction_increasing")
        if age_direction == "down": evidence.append("biological_age_decreasing")
        if abnormal_direction == "down": evidence.append("abnormal_fraction_decreasing")
        if age_direction == "up" and abnormal_direction == "up": trend = "accelerated_aging"
        elif age_direction == "up" or abnormal_direction == "up": trend = "aging"
        elif age_direction == "down" and abnormal_direction == "down": trend = "improving"
        elif age_direction == "flat" and abnormal_direction == "flat": trend = "stable"
        else: trend = "uncertain"
        completeness = min(len(age_values), len(abnormal_values)) / len(observations)
        confidence = round(min(1.0, 0.5 + 0.1 * min(len(observations), 5)) * completeness, 3)
        if trend == "uncertain": confidence = round(confidence * 0.5, 3)
        return {"region_id": region_id, "trend": trend, "confidence": confidence,
                "observation_count": len(observations), "evidence": evidence}

    def get_region_trend_evidence(self, region_id: str) -> Dict[str, Any]:
        """Return auditable measurements supporting a region trend classification."""
        analysis = self.analyze_region_trend(region_id)
        return {
            "region_id": region_id,
            "trend": analysis["trend"],
            "confidence": analysis["confidence"],
            "observation_count": analysis["observation_count"],
            "evidence": analysis["evidence"],
            "measurements": {
                "biological_age": self.get_region_trajectory(region_id, "biological_age"),
                "abnormal_fraction": self.get_region_trajectory(region_id, "abnormal_fraction"),
            },
        }

    def assess_region_data_quality(self, region_id: str) -> Dict[str, Any]:
        """Assess completeness and consistency of longitudinal region data."""
        observations = [point.region_state.get(region_id, {}) for point in self.timepoints]
        observations = [region for region in observations if region]
        if not observations:
            return {"region_id": region_id, "quality_level": "low", "quality_score": 0.0,
                    "observation_count": 0, "missing_fraction": 1.0, "consistency": 0.0}
        required = ("biological_age", "abnormal_fraction")
        present = sum(1 for region in observations for key in required if isinstance(region.get(key), (int, float)))
        expected = len(observations) * len(required)
        completeness = present / expected if expected else 0.0
        confidences = [float(region["confidence"]) for region in observations if isinstance(region.get("confidence"), (int, float))]
        mean_confidence = sum(confidences) / len(confidences) if confidences else 0.0
        missing_fraction = 1.0 - completeness
        series = []
        for key in required:
            values = [float(region[key]) for region in observations if isinstance(region.get(key), (int, float))]
            if len(values) >= 2:
                series.append(values)
        consistency_scores = []
        for values in series:
            if len(values) < 3:
                consistency_scores.append(0.75)
                continue
            steps = [b - a for a, b in zip(values, values[1:])]
            non_mixed = sum(1 for a, b in zip(steps, steps[1:]) if a == 0 or b == 0 or (a > 0) == (b > 0))
            consistency_scores.append(non_mixed / max(1, len(steps) - 1))
        consistency = sum(consistency_scores) / len(consistency_scores) if consistency_scores else 0.0
        quality_score = round(0.5 * completeness + 0.3 * mean_confidence + 0.2 * consistency, 3)
        quality_level = "high" if quality_score >= 0.8 else "medium" if quality_score >= 0.55 else "low"
        return {"region_id": region_id, "quality_level": quality_level, "quality_score": quality_score,
                "observation_count": len(observations), "missing_fraction": round(missing_fraction, 3),
                "mean_confidence": round(mean_confidence, 3), "consistency": round(consistency, 3)}

    def assess_region_risk_signal(self, region_id: str) -> Dict[str, Any]:
        """Generate an explainable risk signal, not a medical diagnosis."""
        trend = self.analyze_region_trend(region_id)
        quality = self.assess_region_data_quality(region_id)
        evidence = list(trend["evidence"])
        quality_level = quality["quality_level"]
        if quality_level == "low":
            return {"region_id": region_id, "signal": "insufficient_data", "severity": "unknown",
                    "confidence": min(trend["confidence"], quality["quality_score"]),
                    "evidence": evidence, "requires_review": False, "data_quality": quality}
        if trend["trend"] == "accelerated_aging":
            signal, severity = "accelerated_change", "moderate"
            evidence.append("longitudinal_acceleration")
        elif trend["trend"] == "aging":
            signal, severity = "aging_change", "mild"
        elif trend["trend"] == "deteriorating":
            signal, severity = "deteriorating_change", "moderate"
        elif trend["trend"] == "improving":
            signal, severity = "improving_change", "informational"
        elif trend["trend"] == "stable":
            signal, severity = "stable", "informational"
        else:
            signal, severity = "uncertain_change", "unknown"
        confidence = round(min(trend["confidence"], quality["quality_score"]), 3)
        return {"region_id": region_id, "signal": signal, "severity": severity,
                "confidence": confidence, "evidence": evidence,
                "requires_review": severity in {"moderate", "high"} and confidence >= 0.6,
                "data_quality": quality}

    def to_dict(self) -> Dict[str, Any]:
        """Convert temporal state to dictionary."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TemporalState":
        """Reconstruct TemporalState."""
        points = [TimePoint(**point) for point in data.get("timepoints", [])]
        return cls(timepoints=points, current_timepoint=data.get("current_timepoint"), metadata=data.get("metadata", {}))
