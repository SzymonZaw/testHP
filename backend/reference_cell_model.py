"""Small deterministic CellModel used to validate the ML integration path."""
from __future__ import annotations

from .ml_contracts import ModelInput, ModelOutput


class ReferenceCellModel:
    """Reference implementation, not a diagnostic model.

    It deliberately uses simple feature thresholds so the full inference
    contract can be exercised without a ML framework or model checkpoint.
    """

    model_id = "reference-cell-model"
    model_version = "0.1.0"

    def predict(self, model_input: ModelInput) -> ModelOutput:
        model_input.validate()
        features = model_input.features
        damage = _number(features.get("damage_score"), 0.0)
        inflammation = _number(features.get("inflammation_score"), 0.0)
        senescence = _number(features.get("senescence_score"), 0.0)

        pathological = max(damage, inflammation)
        if pathological >= 0.8:
            prediction = "pathological"
        elif senescence >= 0.8:
            prediction = "senescent"
        elif pathological >= 0.4:
            prediction = "stressed"
        else:
            prediction = "normal"

        probabilities = {
            "normal": max(0.0, 1.0 - pathological - senescence),
            "stressed": min(pathological, 0.4),
            "pathological": min(pathological, 1.0),
            "senescent": min(senescence, 1.0),
        }
        total = sum(probabilities.values())
        if total:
            probabilities = {key: value / total for key, value in probabilities.items()}

        return ModelOutput(
            model_id=self.model_id,
            model_version=self.model_version,
            prediction=prediction,
            probabilities=probabilities,
            confidence=max(probabilities.values()),
            metadata={"kind": "reference", "framework": "none"},
        )


def _number(value: object, default: float) -> float:
    return float(value) if isinstance(value, (int, float)) and not isinstance(value, bool) else default
