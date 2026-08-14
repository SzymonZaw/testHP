from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Any


@dataclass
class PipelineEvaluation:
    status: str
    readiness: float
    observations: int
    modalities: list[str]
    warnings: list[str]
    limitations: list[str]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def evaluate_pipeline(*, observations: list[Any], modalities: list[str], warnings: list[str] | None = None) -> PipelineEvaluation:
    warnings = list(warnings or [])
    limitations: list[str] = []
    if not observations:
        limitations.append("No observations available.")
    if len(modalities) < 2:
        limitations.append("Multimodal evaluation is limited because fewer than two modalities are present.")
    # Readiness is an engineering/data-readiness score, not a medical accuracy score.
    completeness = min(1.0, len(observations) / 10.0)
    modality_score = min(1.0, len(modalities) / 3.0)
    readiness = round(0.6 * completeness + 0.4 * modality_score, 3)
    status = "ready" if observations and not limitations else "limited"
    return PipelineEvaluation(status, readiness, len(observations), sorted(set(modalities)), warnings, limitations)
