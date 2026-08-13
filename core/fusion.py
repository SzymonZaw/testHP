"""Quality-aware multimodal evidence fusion."""

from dataclasses import dataclass
from typing import Iterable

from .quality import QualityAssessment


@dataclass(frozen=True)
class Evidence:
    modality: str
    feature: str
    value: float
    quality: QualityAssessment


@dataclass(frozen=True)
class FusedFeature:
    feature: str
    value: float
    total_weight: float
    modalities: tuple[str, ...]


class MultimodalFusionEngine:
    """Combine comparable evidence while retaining modality provenance."""

    def fuse(self, evidence: Iterable[Evidence]) -> list[FusedFeature]:
        grouped: dict[str, list[Evidence]] = {}
        for item in evidence:
            if item.quality.usable and item.quality.score > 0:
                grouped.setdefault(item.feature, []).append(item)

        results: list[FusedFeature] = []
        for feature, items in grouped.items():
            total_weight = sum(item.quality.score for item in items)
            value = sum(item.value * item.quality.score for item in items) / total_weight
            modalities = tuple(dict.fromkeys(item.modality for item in items))
            results.append(FusedFeature(feature, value, total_weight, modalities))
        return results
