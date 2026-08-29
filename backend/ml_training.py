"""Training orchestration for leakage-safe cell ML datasets."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Mapping, Sequence

from .ml_contracts import CellModel, ModelInput
from .ml_data_pipeline import RealDataset


@dataclass(frozen=True)
class TrainingConfig:
    dataset_id: str
    dataset_version: str
    task: str
    seed: int = 0
    hyperparameters: Mapping[str, object] = field(default_factory=dict)


@dataclass(frozen=True)
class TrainingRun:
    run_id: str
    model_id: str
    model_version: str
    dataset_id: str
    dataset_version: str
    train_count: int
    validation_count: int
    test_count: int
    metrics: Mapping[str, float] = field(default_factory=dict)


class TrainingPipeline:
    """Framework-neutral training orchestration around a model's fit method."""

    def __init__(self, model: CellModel, run_id_factory: Callable[[], str] | None = None) -> None:
        self.model = model
        self._run_id_factory = run_id_factory or (lambda: f"run-{self.model.model_id}-{self.model.model_version}")

    def _rows(self, dataset: RealDataset, inputs: Mapping[str, ModelInput]) -> dict[str, list]:
        dataset.validate()
        rows = {"train": [], "validation": [], "test": []}
        for sample in dataset.samples:
            if sample.observation_id not in inputs:
                raise KeyError(f"missing ModelInput: {sample.observation_id}")
            rows[sample.split].append(sample)
        return rows

    def _validate_config(self, dataset: RealDataset, config: TrainingConfig) -> None:
        if dataset.dataset_id != config.dataset_id or dataset.version != config.dataset_version:
            raise ValueError("training config does not match dataset")

    def train_classifier(
        self,
        dataset: RealDataset,
        inputs: Mapping[str, ModelInput],
        labels: Mapping[str, int],
        *,
        config: TrainingConfig,
    ) -> TrainingRun:
        rows = self._rows(dataset, inputs)
        self._validate_config(dataset, config)
        train_inputs = [inputs[row.observation_id] for row in rows["train"]]
        train_labels = [labels[row.sample_id] for row in rows["train"]]
        if any(row.sample_id not in labels for row in dataset.samples):
            raise KeyError("missing one or more classification labels")
        fit = getattr(self.model, "fit", None)
        if fit is None:
            raise TypeError("model does not expose fit(inputs, labels)")
        fit(train_inputs, train_labels)
        return TrainingRun(self._run_id_factory(), self.model.model_id, self.model.model_version, dataset.dataset_id, dataset.version, len(rows["train"]), len(rows["validation"]), len(rows["test"]))

    def train_regressor(
        self,
        dataset: RealDataset,
        inputs: Mapping[str, ModelInput],
        targets: Mapping[str, float],
        *,
        config: TrainingConfig,
    ) -> TrainingRun:
        rows = self._rows(dataset, inputs)
        self._validate_config(dataset, config)
        if any(row.sample_id not in targets for row in dataset.samples):
            raise KeyError("missing one or more regression targets")
        train_inputs = [inputs[row.observation_id] for row in rows["train"]]
        train_targets = [float(targets[row.sample_id]) for row in rows["train"]]
        fit = getattr(self.model, "fit", None)
        if fit is None:
            raise TypeError("model does not expose fit(inputs, targets)")
        fit(train_inputs, train_targets)
        return TrainingRun(self._run_id_factory(), self.model.model_id, self.model.model_version, dataset.dataset_id, dataset.version, len(rows["train"]), len(rows["validation"]), len(rows["test"]))

    def train(self, dataset: RealDataset, inputs: Mapping[str, ModelInput], labels: Mapping[str, int], *, config: TrainingConfig) -> TrainingRun:
        """Backward-compatible alias for binary classification training."""
        return self.train_classifier(dataset, inputs, labels, config=config)
