"""Map abnormal signals to useful next measurements."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Mapping

from anomaly.detector import Anomaly


@dataclass(frozen=True)
class InvestigationPlan:
    priority: str
    recommended_modalities: tuple[str, ...]
    reasons: tuple[str, ...]
    unresolved_signals: tuple[str, ...]


class InvestigationPlanner:
    """Rule-based planner; recommendations are hypotheses for data collection, not medical orders."""

    def __init__(self, rules: Mapping[str, tuple[str, ...]] | None = None) -> None:
        self.rules = dict(rules or {
            "cell": ("cell_imaging", "tissue_imaging"),
            "tissue": ("high_resolution_tissue_imaging", "histology"),
            "rna": ("transcriptomics_repeat", "cell_imaging"),
            "fibrosis": ("tissue_imaging", "organ_imaging"),
            "cell_density": ("cell_imaging", "tissue_imaging"),
        })

    def plan(self, anomalies: Iterable[Anomaly], risk_level: str = "none") -> InvestigationPlan:
        items = list(anomalies)
        modalities: list[str] = []
        reasons: list[str] = []
        unresolved: list[str] = []

        for item in items:
            matches = self.rules.get(item.feature)
            if matches is None:
                prefix = item.feature.split("_", 1)[0]
                matches = self.rules.get(prefix, ())
            if not matches:
                unresolved.append(item.feature)
                continue
            for modality in matches:
                if modality not in modalities:
                    modalities.append(modality)
            reasons.append(f"{item.feature}: follow-up for {item.reason}")

        priority = "urgent" if risk_level == "high" else "routine" if items else "none"
        return InvestigationPlan(
            priority=priority,
            recommended_modalities=tuple(modalities),
            reasons=tuple(reasons),
            unresolved_signals=tuple(unresolved),
        )
