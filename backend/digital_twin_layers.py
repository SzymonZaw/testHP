"""Research layers for the hand digital twin beyond cell-level ML.

These contracts are deliberately framework- and therapy-agnostic. They provide
an auditable path from multimodal evidence to multiscale state, longitudinal
trajectories, counterfactual simulations and decision support. They do not
claim clinical validity and never turn a simulation into a treatment order.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from statistics import mean
from typing import Any, Mapping, Protocol, Sequence


@dataclass(frozen=True)
class ModalityEmbedding:
    """Validated representation produced by one data modality."""

    modality: str
    source_ids: tuple[str, ...]
    features: Mapping[str, float]
    quality: float | None = None
    uncertainty: float | None = None
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def validate(self) -> None:
        if not self.modality or not self.source_ids:
            raise ValueError("modality and source_ids are required")
        if not self.features:
            raise ValueError("modality embedding requires features")
        if self.quality is not None and not 0 <= self.quality <= 1:
            raise ValueError("quality must be between 0 and 1")
        if self.uncertainty is not None and self.uncertainty < 0:
            raise ValueError("uncertainty cannot be negative")
        for name, value in self.features.items():
            if not isinstance(value, (int, float)) or isinstance(value, bool):
                raise ValueError(f"feature {name!r} must be numeric")


@dataclass(frozen=True)
class MultimodalRepresentation:
    """Fused representation while retaining per-modality provenance."""

    fusion_id: str
    subject_id: str
    hand_id: str
    timepoint_id: str
    modalities: tuple[ModalityEmbedding, ...]
    fused_features: Mapping[str, float]
    fusion_method: str
    confidence: float | None = None
    uncertainty: float | None = None
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def validate(self) -> None:
        if not self.fusion_id or not self.subject_id or not self.hand_id or not self.timepoint_id:
            raise ValueError("fusion identity is required")
        if not self.modalities or not self.fused_features:
            raise ValueError("multimodal representation requires modalities and fused features")
        if not self.fusion_method:
            raise ValueError("fusion_method is required")
        for item in self.modalities:
            item.validate()
        if self.confidence is not None and not 0 <= self.confidence <= 1:
            raise ValueError("confidence must be between 0 and 1")
        if self.uncertainty is not None and self.uncertainty < 0:
            raise ValueError("uncertainty cannot be negative")


class MultimodalFusion(Protocol):
    fusion_id: str
    fusion_version: str

    def fuse(self, embeddings: Sequence[ModalityEmbedding], *, subject_id: str, hand_id: str, timepoint_id: str) -> MultimodalRepresentation:
        ...


class MeanFeatureFusion:
    """Simple deterministic fusion baseline; production models can replace it."""

    fusion_id = "mean-feature-fusion"
    fusion_version = "0.1.0"

    def fuse(self, embeddings: Sequence[ModalityEmbedding], *, subject_id: str, hand_id: str, timepoint_id: str) -> MultimodalRepresentation:
        if not embeddings:
            raise ValueError("embeddings must be non-empty")
        for item in embeddings:
            item.validate()
        names = sorted({name for item in embeddings for name in item.features})
        fused = {name: mean(float(item.features.get(name, 0.0)) for item in embeddings) for name in names}
        quality = mean(item.quality for item in embeddings if item.quality is not None) if any(item.quality is not None for item in embeddings) else None
        uncertainty = mean(item.uncertainty for item in embeddings if item.uncertainty is not None) if any(item.uncertainty is not None for item in embeddings) else None
        result = MultimodalRepresentation(
            fusion_id=self.fusion_id,
            subject_id=subject_id,
            hand_id=hand_id,
            timepoint_id=timepoint_id,
            modalities=tuple(embeddings),
            fused_features=fused,
            fusion_method=self.fusion_id,
            confidence=quality,
            uncertainty=uncertainty,
        )
        result.validate()
        return result


@dataclass(frozen=True)
class ScaleAssessment:
    """Assessment at one anatomical scale."""

    scale: str
    object_id: str
    parent_id: str | None
    state: str
    biological_age: float | None = None
    risk_score: float | None = None
    confidence: float | None = None
    uncertainty: float | None = None
    child_ids: tuple[str, ...] = ()
    evidence_ids: tuple[str, ...] = ()

    def validate(self) -> None:
        if self.scale not in {"cell", "population", "micro-region", "tissue", "region", "hand"}:
            raise ValueError("unsupported anatomical scale")
        if not self.object_id or not self.state:
            raise ValueError("object_id and state are required")
        if self.biological_age is not None and self.biological_age < 0:
            raise ValueError("biological_age cannot be negative")
        if self.risk_score is not None and not 0 <= self.risk_score <= 1:
            raise ValueError("risk_score must be between 0 and 1")
        if self.confidence is not None and not 0 <= self.confidence <= 1:
            raise ValueError("confidence must be between 0 and 1")
        if self.uncertainty is not None and self.uncertainty < 0:
            raise ValueError("uncertainty cannot be negative")


@dataclass(frozen=True)
class MultiscaleTwinState:
    """Consistent snapshot from cells through the complete hand."""

    snapshot_id: str
    subject_id: str
    hand_id: str
    timepoint_id: str
    assessments: tuple[ScaleAssessment, ...]
    aggregation_method: str
    confidence: float | None = None
    uncertainty: float | None = None

    def validate(self) -> None:
        if not self.snapshot_id or not self.subject_id or not self.hand_id or not self.timepoint_id:
            raise ValueError("snapshot identity is required")
        if not self.assessments or not self.aggregation_method:
            raise ValueError("assessments and aggregation_method are required")
        for item in self.assessments:
            item.validate()
            if item.scale != "cell" and item.parent_id is None and item.scale != "hand":
                raise ValueError("non-cell assessments require a parent")
        if self.confidence is not None and not 0 <= self.confidence <= 1:
            raise ValueError("confidence must be between 0 and 1")
        if self.uncertainty is not None and self.uncertainty < 0:
            raise ValueError("uncertainty cannot be negative")


class MultiscaleAggregator:
    """Deterministic baseline aggregator for the hierarchy already in the domain."""

    aggregation_method = "hierarchical-weighted-mean"
    aggregation_version = "0.1.0"

    def aggregate(self, assessments: Sequence[ScaleAssessment], *, snapshot_id: str, subject_id: str, hand_id: str, timepoint_id: str) -> MultiscaleTwinState:
        if not assessments:
            raise ValueError("assessments must be non-empty")
        for item in assessments:
            item.validate()
        confidences = [item.confidence for item in assessments if item.confidence is not None]
        uncertainties = [item.uncertainty for item in assessments if item.uncertainty is not None]
        state = MultiscaleTwinState(
            snapshot_id=snapshot_id,
            subject_id=subject_id,
            hand_id=hand_id,
            timepoint_id=timepoint_id,
            assessments=tuple(assessments),
            aggregation_method=self.aggregation_method,
            confidence=mean(confidences) if confidences else None,
            uncertainty=mean(uncertainties) if uncertainties else None,
        )
        state.validate()
        return state


@dataclass(frozen=True)
class LongitudinalObservation:
    """One comparable twin snapshot in an ordered time series."""

    timepoint_id: str
    timestamp: str
    snapshot_id: str
    state_score: float
    biological_age: float | None = None
    risk_score: float | None = None
    confidence: float | None = None

    def validate(self) -> None:
        if not self.timepoint_id or not self.timestamp or not self.snapshot_id:
            raise ValueError("longitudinal observation identity is required")
        if not 0 <= self.state_score <= 1:
            raise ValueError("state_score must be between 0 and 1")
        if self.biological_age is not None and self.biological_age < 0:
            raise ValueError("biological_age cannot be negative")
        if self.risk_score is not None and not 0 <= self.risk_score <= 1:
            raise ValueError("risk_score must be between 0 and 1")
        if self.confidence is not None and not 0 <= self.confidence <= 1:
            raise ValueError("confidence must be between 0 and 1")


@dataclass(frozen=True)
class LongitudinalTwin:
    """Versioned history for one hand."""

    twin_id: str
    subject_id: str
    hand_id: str
    observations: tuple[LongitudinalObservation, ...]
    model_version: str

    def validate(self) -> None:
        if not self.twin_id or not self.subject_id or not self.hand_id or not self.model_version:
            raise ValueError("twin identity is required")
        if not self.observations:
            raise ValueError("longitudinal twin requires observations")
        timestamps = [item.timestamp for item in self.observations]
        if timestamps != sorted(timestamps):
            raise ValueError("observations must be chronologically ordered")
        for item in self.observations:
            item.validate()

    @property
    def latest(self) -> LongitudinalObservation:
        self.validate()
        return self.observations[-1]


@dataclass(frozen=True)
class FutureStatePrediction:
    """Probabilistic projection of a future twin state."""

    prediction_id: str
    twin_id: str
    horizon: str
    predicted_state_score: float
    predicted_biological_age: float | None
    risk_score: float | None
    uncertainty: float
    model_id: str
    model_version: str
    assumptions: tuple[str, ...] = ()

    def validate(self) -> None:
        if not self.prediction_id or not self.twin_id or not self.horizon or not self.model_id or not self.model_version:
            raise ValueError("prediction identity is required")
        if not 0 <= self.predicted_state_score <= 1:
            raise ValueError("predicted_state_score must be between 0 and 1")
        if self.predicted_biological_age is not None and self.predicted_biological_age < 0:
            raise ValueError("predicted_biological_age cannot be negative")
        if self.risk_score is not None and not 0 <= self.risk_score <= 1:
            raise ValueError("risk_score must be between 0 and 1")
        if self.uncertainty < 0:
            raise ValueError("uncertainty cannot be negative")


class FutureStateModel(Protocol):
    model_id: str
    model_version: str

    def predict(self, twin: LongitudinalTwin, *, horizon: str) -> FutureStatePrediction:
        ...


class TrendFutureStateModel:
    """Simple research baseline using the recent linear trend."""

    model_id = "trend-future-state"
    model_version = "0.1.0"

    def predict(self, twin: LongitudinalTwin, *, horizon: str) -> FutureStatePrediction:
        twin.validate()
        latest = twin.latest
        if len(twin.observations) == 1:
            projected = latest.state_score
        else:
            previous = twin.observations[-2]
            projected = min(1.0, max(0.0, latest.state_score + (latest.state_score - previous.state_score)))
        uncertainty = max(0.05, 1.0 - (latest.confidence or 0.5))
        result = FutureStatePrediction(
            prediction_id=f"future-{twin.twin_id}-{horizon}",
            twin_id=twin.twin_id,
            horizon=horizon,
            predicted_state_score=projected,
            predicted_biological_age=latest.biological_age,
            risk_score=latest.risk_score,
            uncertainty=uncertainty,
            model_id=self.model_id,
            model_version=self.model_version,
            assumptions=("recent trend is representative",),
        )
        result.validate()
        return result


@dataclass(frozen=True)
class InterventionScenario:
    """Counterfactual input; no assertion that an intervention is effective."""

    scenario_id: str
    name: str
    target_scales: tuple[str, ...]
    parameter_changes: Mapping[str, float]
    assumptions: tuple[str, ...] = ()

    def validate(self) -> None:
        if not self.scenario_id or not self.name or not self.target_scales:
            raise ValueError("scenario identity and target_scales are required")
        if any(scale not in {"cell", "population", "micro-region", "tissue", "region", "hand"} for scale in self.target_scales):
            raise ValueError("scenario contains unsupported scale")
        for name, value in self.parameter_changes.items():
            if not isinstance(value, (int, float)) or isinstance(value, bool):
                raise ValueError(f"scenario parameter {name!r} must be numeric")


@dataclass(frozen=True)
class InterventionSimulation:
    """Counterfactual projection of a twin under an explicit scenario."""

    simulation_id: str
    twin_id: str
    scenario: InterventionScenario
    baseline_prediction: FutureStatePrediction
    simulated_state_score: float
    simulated_risk_score: float | None
    uncertainty: float
    model_id: str
    model_version: str

    def validate(self) -> None:
        if not self.simulation_id or not self.twin_id or not self.model_id or not self.model_version:
            raise ValueError("simulation identity is required")
        self.scenario.validate()
        self.baseline_prediction.validate()
        if not 0 <= self.simulated_state_score <= 1:
            raise ValueError("simulated_state_score must be between 0 and 1")
        if self.simulated_risk_score is not None and not 0 <= self.simulated_risk_score <= 1:
            raise ValueError("simulated_risk_score must be between 0 and 1")
        if self.uncertainty < 0:
            raise ValueError("uncertainty cannot be negative")


class InterventionSimulator:
    """Transparent counterfactual baseline, intentionally not a treatment model."""

    model_id = "counterfactual-linear-baseline"
    model_version = "0.1.0"

    def simulate(self, twin: LongitudinalTwin, prediction: FutureStatePrediction, scenario: InterventionScenario) -> InterventionSimulation:
        twin.validate()
        prediction.validate()
        scenario.validate()
        delta = sum(float(value) for value in scenario.parameter_changes.values())
        simulated_state = min(1.0, max(0.0, prediction.predicted_state_score - delta))
        simulated_risk = None if prediction.risk_score is None else min(1.0, max(0.0, prediction.risk_score - delta))
        result = InterventionSimulation(
            simulation_id=f"simulation-{scenario.scenario_id}-{prediction.prediction_id}",
            twin_id=twin.twin_id,
            scenario=scenario,
            baseline_prediction=prediction,
            simulated_state_score=simulated_state,
            simulated_risk_score=simulated_risk,
            uncertainty=prediction.uncertainty + abs(delta) * 0.1,
            model_id=self.model_id,
            model_version=self.model_version,
        )
        result.validate()
        return result


@dataclass(frozen=True)
class DecisionSupportAssessment:
    """Evidence-linked prioritization; it is not a clinical treatment order."""

    assessment_id: str
    twin_id: str
    priority: str
    risk_score: float | None
    confidence: float | None
    evidence_ids: tuple[str, ...]
    rationale: tuple[str, ...]
    requires_human_review: bool = True
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def validate(self) -> None:
        if not self.assessment_id or not self.twin_id or not self.priority:
            raise ValueError("decision-support identity is required")
        if self.priority not in {"no_action", "monitor", "investigate", "intervention_candidate", "insufficient_evidence"}:
            raise ValueError("unsupported decision-support priority")
        if self.risk_score is not None and not 0 <= self.risk_score <= 1:
            raise ValueError("risk_score must be between 0 and 1")
        if self.confidence is not None and not 0 <= self.confidence <= 1:
            raise ValueError("confidence must be between 0 and 1")
        if not self.evidence_ids:
            raise ValueError("decision support requires evidence_ids")


class DecisionSupportEngine:
    """Conservative prioritization baseline based on predicted risk and uncertainty."""

    engine_id = "research-decision-support"
    engine_version = "0.1.0"

    def assess(self, twin: LongitudinalTwin, prediction: FutureStatePrediction, *, evidence_ids: Sequence[str]) -> DecisionSupportAssessment:
        twin.validate()
        prediction.validate()
        evidence = tuple(evidence_ids)
        if not evidence:
            raise ValueError("evidence_ids are required")
        risk = prediction.risk_score
        if risk is None:
            priority = "insufficient_evidence"
            rationale = ("future risk was not quantified",)
        elif prediction.uncertainty >= 0.5:
            priority = "investigate"
            rationale = ("prediction uncertainty is high",)
        elif risk >= 0.8:
            priority = "intervention_candidate"
            rationale = ("predicted risk is high; human review required",)
        elif risk >= 0.4:
            priority = "monitor"
            rationale = ("predicted risk warrants monitoring",)
        else:
            priority = "no_action"
            rationale = ("predicted risk is currently low",)
        result = DecisionSupportAssessment(
            assessment_id=f"decision-{twin.twin_id}-{prediction.prediction_id}",
            twin_id=twin.twin_id,
            priority=priority,
            risk_score=risk,
            confidence=max(0.0, min(1.0, 1.0 - prediction.uncertainty)),
            evidence_ids=evidence,
            rationale=rationale,
            requires_human_review=True,
            metadata={"engine_id": self.engine_id, "engine_version": self.engine_version},
        )
        result.validate()
        return result
