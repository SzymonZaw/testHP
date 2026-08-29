"""End-to-end orchestration from cell observations to digital-twin decisions.

This module composes the existing domain, ML, multimodal, multiscale,
longitudinal, simulation and decision-support layers. It deliberately keeps
all stages explicit and auditable; it does not make clinical treatment orders.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

from .cell_observation import CellObservation
from .digital_twin_layers import (
    DecisionSupportAssessment,
    FutureStatePrediction,
    InterventionScenario,
    InterventionSimulation,
    LongitudinalTwin,
    ModalityEmbedding,
    MultimodalFusion,
    MultimodalRepresentation,
    MultiscaleAggregator,
    MultiscaleTwinState,
    FutureStateModel,
    InterventionSimulator,
)
from .ml_contracts import ModelInput
from .ml_inference import CellInferenceService, InferenceResult
from .ml_data_pipeline import (
    BaselinePreprocessor,
    BaselineRealFeatureExtractor,
    ImageInput,
    OmicsInput,
    ProcessedCellData,
)


@dataclass(frozen=True)
class CellPipelineResult:
    """All auditable outputs produced for one cell observation."""

    processed: ProcessedCellData
    model_input: ModelInput
    inference: InferenceResult


@dataclass(frozen=True)
class DigitalTwinPipelineResult:
    """End-to-end output of one twin update."""

    cell_results: tuple[CellPipelineResult, ...]
    multimodal: MultimodalRepresentation | None
    multiscale: MultiscaleTwinState | None
    future_state: FutureStatePrediction | None
    intervention: InterventionSimulation | None
    decision: DecisionSupportAssessment | None


class DigitalTwinPipeline:
    """Compose the project's existing layers into one explicit execution path."""

    def __init__(
        self,
        inference_service: CellInferenceService,
        *,
        preprocessor: BaselinePreprocessor | None = None,
        feature_extractor: BaselineRealFeatureExtractor | None = None,
        fusion: MultimodalFusion | None = None,
        multiscale: MultiscaleAggregator | None = None,
        future_model: FutureStateModel | None = None,
        simulator: InterventionSimulator | None = None,
    ) -> None:
        self.inference_service = inference_service
        self.preprocessor = preprocessor or BaselinePreprocessor()
        self.feature_extractor = feature_extractor or BaselineRealFeatureExtractor()
        self.fusion = fusion
        self.multiscale = multiscale
        self.future_model = future_model
        self.simulator = simulator

    def assess_cells(
        self,
        observations: Sequence[CellObservation],
        *,
        model_id: str,
        model_version: str | None = None,
        images: Sequence[ImageInput] = (),
        omics: Sequence[OmicsInput] = (),
    ) -> tuple[CellPipelineResult, ...]:
        """Run preprocessing, feature extraction and registered cell inference."""
        results: list[CellPipelineResult] = []
        for observation in observations:
            processed = self.preprocessor.process(observation, images=images, omics=omics)
            model_input = self.feature_extractor.extract(processed)
            inference = self.inference_service.predict_input(
                observation,
                model_input,
                model_id=model_id,
                model_version=model_version,
            )
            results.append(CellPipelineResult(processed, model_input, inference))
        return tuple(results)

    def run_update(
        self,
        observations: Sequence[CellObservation],
        *,
        model_id: str,
        model_version: str | None = None,
        images: Sequence[ImageInput] = (),
        omics: Sequence[OmicsInput] = (),
        modality_embeddings: Sequence[ModalityEmbedding] = (),
        subject_id: str | None = None,
        hand_id: str | None = None,
        timepoint_id: str | None = None,
        multiscale_assessments=(),
        twin: LongitudinalTwin | None = None,
        horizon: str | None = None,
        scenario: InterventionScenario | None = None,
        evidence_ids: Sequence[str] = (),
    ) -> DigitalTwinPipelineResult:
        """Execute the available pipeline layers in dependency order."""
        cells = self.assess_cells(
            observations,
            model_id=model_id,
            model_version=model_version,
            images=images,
            omics=omics,
        )

        multimodal = None
        if self.fusion is not None and modality_embeddings:
            if not subject_id or not hand_id or not timepoint_id:
                raise ValueError("subject_id, hand_id and timepoint_id are required for fusion")
            multimodal = self.fusion.fuse(
                modality_embeddings,
                subject_id=subject_id,
                hand_id=hand_id,
                timepoint_id=timepoint_id,
            )

        multiscale = None
        if self.multiscale is not None and multiscale_assessments:
            if not subject_id or not hand_id or not timepoint_id:
                raise ValueError("subject_id, hand_id and timepoint_id are required for multiscale aggregation")
            multiscale = self.multiscale.aggregate(
                multiscale_assessments,
                snapshot_id=f"snapshot-{timepoint_id}",
                subject_id=subject_id,
                hand_id=hand_id,
                timepoint_id=timepoint_id,
            )

        future_state = None
        if self.future_model is not None and twin is not None and horizon:
            future_state = self.future_model.predict(twin, horizon=horizon)

        intervention = None
        if self.simulator is not None and twin is not None and future_state is not None and scenario is not None:
            intervention = self.simulator.simulate(twin, future_state, scenario)

        decision = None
        if twin is not None and future_state is not None:
            from .digital_twin_layers import DecisionSupportEngine

            engine = DecisionSupportEngine()
            risk = future_state.risk_score
            if intervention is not None:
                risk = intervention.simulated_risk_score
            decision = engine.assess(
                twin,
                risk_score=risk,
                confidence=max(0.0, 1.0 - future_state.uncertainty),
                evidence_ids=evidence_ids,
            )

        return DigitalTwinPipelineResult(
            cell_results=cells,
            multimodal=multimodal,
            multiscale=multiscale,
            future_state=future_state,
            intervention=intervention,
            decision=decision,
        )
