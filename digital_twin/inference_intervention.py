"""Conservative attention priorities derived from hierarchical inference."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Iterable, List


@dataclass(frozen=True)
class InferenceAttention:
    level: str
    identifier: str
    priority: str
    score: float
    reason: str
    cells: int
    hotspot_score: float
    confidence: float | None
    uncertainty: float | None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "level": self.level,
            "identifier": self.identifier,
            "priority": self.priority,
            "score": self.score,
            "reason": self.reason,
            "cells": self.cells,
            "hotspot_score": self.hotspot_score,
            "confidence": self.confidence,
            "uncertainty": self.uncertainty,
        }


def build_inference_attention(groups: Dict[str, Dict[str, Any]]) -> List[InferenceAttention]:
    """Rank hierarchy nodes for further observation; this is not a treatment decision."""
    result: List[InferenceAttention] = []
    for level, nodes in groups.items():
        for identifier, node in nodes.items():
            hotspot = max(0.0, min(1.0, float(node.hotspot_score)))
            abrupt = int(node.abrupt_changes)
            cells = int(node.cells)
            confidence = node.mean_confidence
            uncertainty = 1.0 - confidence if confidence is not None else None
            score = min(1.0, hotspot + min(abrupt / max(cells, 1), 0.5))
            if cells == 0:
                priority = "monitor"
                reason = "No cell inference evidence is currently available."
            elif score >= 0.6:
                priority = "high_attention"
                reason = "High concentration of abnormal, aging, or abrupt-change signals."
            elif score >= 0.25:
                priority = "investigate"
                reason = "Meaningful concentration of signals warrants closer observation."
            else:
                priority = "monitor"
                reason = "Current evidence does not show a strong local concentration of signals."
            result.append(InferenceAttention(level, identifier, priority, score, reason, cells, hotspot, confidence, uncertainty))
    return sorted(result, key=lambda item: (-item.score, item.level, item.identifier))
