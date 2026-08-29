"""Adapters connecting domain observations to technology-neutral ML contracts."""
from __future__ import annotations

from dataclasses import asdict
from datetime import datetime, timezone
from typing import Any

from .anatomy_foundation import CellStateAssessment, Evidence
from .cell_observation import CellObservation
from .data_foundation import Provenance
from .ml_contracts import ModelInput, ModelOutput


def observation_to_model_input(observation: CellObservation) -> ModelInput:
    """Convert a validated cell observation into a model-ready domain contract."""
    observation.validate()
    features: dict[str, Any] = {}
    features.update(observation.morphology)
    features.update(observation.molecular_features)
    features.update(observation.functional_features)
    return ModelInput(
        sample_id=observation.observation_id,
        modality=observation.modality,
        features=features,
        spatial_reference=observation.spatial_reference,
        quality=observation.quality,
        metadata={
            "cell_id": observation.cell_id,
            "subject_id": observation.subject_id,
            "hand_id": observation.hand_id,
            "timepoint_id": observation.timepoint_id,
            "acquisition_id": observation.acquisition_id,
            "source_data_ids": observation.source_data_ids,
        },
    )


def model_output_to_cell_assessment(
    observation: CellObservation,
    output: ModelOutput,
    *,
    assessed_at: str | None = None,
    provenance: Provenance | None = None,
) -> CellStateAssessment:
    """Convert an ML prediction into the canonical cell assessment contract."""
    observation.validate()
    output.validate()
    state = str(output.prediction)
    allowed = {"normal", "pathological", "stressed", "senescent", "unknown"}
    if state not in allowed:
        raise ValueError(f"unsupported cell assessment state: {state!r}")

    confidence = output.confidence
    if confidence is None and output.probabilities:
        confidence = max(output.probabilities.values())

    evidence = list(observation.evidence)
    evidence.append(
        Evidence(
            evidence_id=f"model:{output.model_id}:{observation.observation_id}",
            source_data_ids=observation.source_data_ids,
            kind="ml_prediction",
            value={
                "prediction": output.prediction,
                "probabilities": dict(output.probabilities),
                "attributions": dict(output.attributions),
                "model_id": output.model_id,
                "model_version": output.model_version,
            },
            confidence=confidence,
            provenance=provenance or Provenance(
                source_object_ids=observation.source_data_ids,
                method=output.model_id,
                method_version=output.model_version,
                processing_timestamp=assessed_at or datetime.now(timezone.utc).isoformat(),
                validation_status="unknown",
            ),
        )
    )

    assessment = CellStateAssessment(
        assessment_id=f"cell-assessment:{observation.observation_id}:{output.model_id}:{output.model_version}",
        cell_id=observation.cell_id,
        state=state,
        confidence=confidence,
        evidence=tuple(evidence),
        provenance=provenance or observation.provenance,
        assessed_at=assessed_at or datetime.now(timezone.utc).isoformat(),
    )
    assessment.validate()
    return assessment


def assessment_metadata(output: ModelOutput) -> dict[str, Any]:
    """Return serializable model provenance metadata for audit storage."""
    output.validate()
    return {
        "model_id": output.model_id,
        "model_version": output.model_version,
        "prediction": output.prediction,
        "probabilities": dict(output.probabilities),
        "confidence": output.confidence,
        "uncertainty": asdict(output.uncertainty),
        "attributions": dict(output.attributions),
        "metadata": dict(output.metadata),
    }
