from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class SegmentationResult:
    segmentation_id: str
    image_id: str
    algorithm_id: str
    algorithm_version: str
    cell_ids: tuple[str, ...]
    expert_annotation_ref: str | None = None
    confidence: float | None = None
    quality_metrics: dict[str, float] = field(default_factory=dict)

    def validate(self) -> None:
        if not self.segmentation_id or not self.image_id or not self.algorithm_id:
            raise ValueError("segmentation identity is incomplete")
        if self.confidence is not None and not 0 <= self.confidence <= 1:
            raise ValueError("confidence must be between 0 and 1")
