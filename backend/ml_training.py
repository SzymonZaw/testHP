"""Training orchestration for leakage-safe cell ML datasets."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Mapping

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

    def train(
        self,
        dataset: RealDataset,
        inputs: Mapping[str, ModelInput],
        labels: Mapping[str, int],
        *,
        config: TrainingConfig,
    ) -> TrainingRun:
        dataset.validate()
        if dataset.dataset_id != config.dataset_id or dataset.version != config.dataset_version:
            raise ValueError("training config does not match dataset")

        split_rows: dict[str, list] = {"train": [], "validation": [], "test": []}
        for sample in dataset.samples:
            if sample.observation_id not in inputs:
                raise KeyError(f"missing ModelInput: {sample.observation_id}")
            if sample.sample_id not in labels:
                raise KeyError(f"missing label: {sample.sample_id}")
            split_rows[sample.split].append(sample)

        train_inputs = [inputs[row.observation_id] for row in split_rows["train"]]
        train_labels = [labels[row.sample_id] for row in split_rows["train"]]
        fit = getattr(self.model, "fit", None)
        if fit is None:
            raise TypeError("model does not expose fit(inputs, labels)")
        fit(train_inputs, train_labels)

        return TrainingRun(
            run_id=self._run_id_factory(),
            model_id=self.model.model_id,
            model_version=self.model.model_version,
            dataset_id=dataset.dataset_id,
            dataset_version=dataset.version,
            train_count=len(split_rows["train"]),
            validation_count=len(split_rows["validation"]),
            test_count=len(split_rows["test"]),
        )
