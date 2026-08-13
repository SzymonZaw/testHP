"""Transparent measurement planning based on uncertainty and modality disagreement."""

from dataclasses import dataclass


@dataclass(frozen=True)
class ModalityEvidence:
    modality: str
    value: float
    uncertainty: float


@dataclass(frozen=True)
class MeasurementSuggestion:
    target_feature: str
    suggested_modality: str
    reason: str


class MeasurementPlanner:
    def suggest(self, target_feature: str, evidence: list[ModalityEvidence], available_modalities: list[str]) -> MeasurementSuggestion | None:
        if not evidence or not available_modalities:
            return None
        worst = max(evidence, key=lambda item: item.uncertainty)
        candidates = [m for m in available_modalities if m != worst.modality]
        if not candidates:
            return None
        return MeasurementSuggestion(target_feature, candidates[0], "additional independent modality may reduce uncertainty")
