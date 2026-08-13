"""Transparent anomaly detection primitives for longitudinal biological data."""

from dataclasses import dataclass
from math import isfinite
from typing import Iterable, Optional


@dataclass(frozen=True)
class AnomalyEvidence:
    feature: str
    value: float
    expected: float
    tolerance: float
    quality_score: float = 1.0
    modality: Optional[str] = None


@dataclass(frozen=True)
class AnomalyResult:
    feature: str
    deviation: float
    score: float
    anomalous: bool
    insufficient_evidence: bool
    modalities: tuple[str, ...] = ()


class AdvancedAnomalyDetector:
    """Detect deviations without interpreting them as diagnoses."""

    def __init__(self, threshold: float = 1.0, minimum_quality: float = 0.5) -> None:
        if threshold <= 0:
            raise ValueError("threshold must be positive")
        if not 0 <= minimum_quality <= 1:
            raise ValueError("minimum_quality must be between 0 and 1")
        self.threshold = threshold
        self.minimum_quality = minimum_quality

    def detect(self, evidence: Iterable[AnomalyEvidence]) -> list[AnomalyResult]:
        grouped: dict[str, list[AnomalyEvidence]] = {}
        for item in evidence:
            if not all(isfinite(v) for v in (item.value, item.expected, item.tolerance, item.quality_score)):
                continue
            if item.tolerance <= 0 or item.quality_score < self.minimum_quality:
                continue
            grouped.setdefault(item.feature, []).append(item)

        results: list[AnomalyResult] = []
        for feature, items in grouped.items():
            deviations = [abs(item.value - item.expected) / item.tolerance for item in items]
            score = max(deviations)
            modalities = tuple(dict.fromkeys(item.modality for item in items if item.modality))
            results.append(
                AnomalyResult(
                    feature=feature,
                    deviation=score,
                    score=score,
                    anomalous=score >= self.threshold,
                    insufficient_evidence=False,
                    modalities=modalities,
                )
            )
        return results

    def assess(self, evidence: Iterable[AnomalyEvidence]) -> list[AnomalyResult]:
        evidence_list = list(evidence)
        results = self.detect(evidence_list)
        seen = {result.feature for result in results}
        features = {item.feature for item in evidence_list}
        for feature in features - seen:
            results.append(
                AnomalyResult(feature, 0.0, 0.0, False, True, ())
            )
        return results
