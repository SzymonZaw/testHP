"""Measurement quality assessment primitives."""

from dataclasses import dataclass
from typing import Iterable, Optional

from .measurement import Measurement
from .observation import Observation


@dataclass(frozen=True)
class QualityAssessment:
    score: float
    flags: tuple[str, ...] = ()
    usable: bool = True


class MeasurementQualityEngine:
    """Apply transparent quality rules without changing the underlying data."""

    def assess_measurement(self, measurement: Measurement) -> QualityAssessment:
        flags: list[str] = []
        if measurement.uncertainty is not None:
            quality = measurement.uncertainty.quality_score
            if quality is not None and quality < 0.5:
                flags.append("low_quality_score")
            flags.extend(measurement.uncertainty.quality_flags)
        else:
            flags.append("missing_uncertainty")

        score = 1.0
        if "missing_uncertainty" in flags:
            score -= 0.2
        if "low_quality_score" in flags:
            score -= 0.4
        score = max(0.0, score)
        return QualityAssessment(score=score, flags=tuple(dict.fromkeys(flags)), usable=score >= 0.5)

    def assess_observation(self, observation: Observation) -> QualityAssessment:
        flags: list[str] = []
        if observation.uncertainty is not None:
            quality = observation.uncertainty.quality_score
            if quality is not None and quality < 0.5:
                flags.append("low_quality_score")
            flags.extend(observation.uncertainty.quality_flags)
        else:
            flags.append("missing_uncertainty")

        score = 1.0
        if "missing_uncertainty" in flags:
            score -= 0.2
        if "low_quality_score" in flags:
            score -= 0.4
        score = max(0.0, score)
        return QualityAssessment(score=score, flags=tuple(dict.fromkeys(flags)), usable=score >= 0.5)

    def assess_many(self, records: Iterable[Measurement | Observation]) -> list[QualityAssessment]:
        return [
            self.assess_measurement(record) if isinstance(record, Measurement) else self.assess_observation(record)
            for record in records
        ]
