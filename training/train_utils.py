"""
train_utils.py

Wspólne narzędzia treningowe dla projektu Doktorat_Kod.

Odpowiada za:
- ustawianie seedów,
- wybór urządzenia CPU/GPU,
- tworzenie DataLoaderów,
- konfigurację optimizerów,
- schedulerów,
- pętle treningowe i walidacyjne,
- early stopping,
- zapisywanie i wczytywanie checkpointów,
- podstawowe metryki klasyfikacyjne,
- obsługę mixed precision,
- liczenie parametrów modelu.

Folder:
    training/

Używany przez:
    train_aging.py
    train_abnormality.py
    train_pathology.py
    train_risk.py
    train_fusion.py
    train_longitudinal.py
"""

from __future__ import annotations

import json
import logging
import math
import os
import random
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any, Callable, Dict, Iterable, List, Mapping, Optional, Sequence, Tuple

import numpy as np
import torch
import torch.nn as nn
from torch.optim import Optimizer
from torch.optim.lr_scheduler import (
    CosineAnnealingLR,
    ReduceLROnPlateau,
    StepLR,
)
from torch.utils.data import DataLoader, Dataset


# ============================================================
# LOGGING
# ============================================================

LOGGER = logging.getLogger(__name__)


def setup_logger(
    name: str = "training",
    level: int = logging.INFO,
) -> logging.Logger:
    """
    Konfiguruje logger używany przez moduły treningowe.
    """

    logger = logging.getLogger(name)

    if not logger.handlers:
        handler = logging.StreamHandler()

        formatter = logging.Formatter(
            fmt="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )

        handler.setFormatter(formatter)
        logger.addHandler(handler)

    logger.setLevel(level)
    logger.propagate = False

    return logger


# ============================================================
# REPRODUCIBILITY
# ============================================================

def set_seed(seed: int = 42) -> None:
    """
    Ustawia seed dla głównych generatorów losowych.

    Parameters
    ----------
    seed:
        Seed eksperymentu.
    """

    random.seed(seed)
    np.random.seed(seed)

    torch.manual_seed(seed)
    torch.cuda.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)

    # Dla maksymalnej powtarzalności.
    torch.backends.cudnn.deterministic = True
    torch.backends.cudnn.benchmark = False


# ============================================================
# DEVICE
# ============================================================

def get_device(
    requested_device: Optional[str] = None,
) -> torch.device:
    """
    Zwraca urządzenie treningowe.

    requested_device:
        "cuda", "cpu", "mps" lub None.

    Jeśli None:
        wybierane jest CUDA -> MPS -> CPU.
    """

    if requested_device is not None:
        requested = requested_device.lower()

        if requested == "cuda":
            if not torch.cuda.is_available():
                LOGGER.warning(
                    "CUDA requested, but CUDA is unavailable. "
                    "Falling back to CPU."
                )
                return torch.device("cpu")

            return torch.device("cuda")

        if requested == "mps":
            mps_available = (
                hasattr(torch.backends, "mps")
                and torch.backends.mps.is_available()
            )

            if not mps_available:
                LOGGER.warning(
                    "MPS requested, but MPS is unavailable. "
                    "Falling back to CPU."
                )
                return torch.device("cpu")

            return torch.device("mps")

        if requested == "cpu":
            return torch.device("cpu")

        raise ValueError(
            f"Unsupported device: {requested_device}"
        )

    if torch.cuda.is_available():
        return torch.device("cuda")

    if (
        hasattr(torch.backends, "mps")
        and torch.backends.mps.is_available()
    ):
        return torch.device("mps")

    return torch.device("cpu")


# ============================================================
# MODEL INFORMATION
# ============================================================

def count_parameters(model: nn.Module) -> int:
    """
    Liczba wszystkich parametrów modelu.
    """

    return sum(
        parameter.numel()
        for parameter in model.parameters()
    )


def count_trainable_parameters(model: nn.Module) -> int:
    """
    Liczba trenowalnych parametrów modelu.
    """

    return sum(
        parameter.numel()
        for parameter in model.parameters()
        if parameter.requires_grad
    )


def model_summary(model: nn.Module) -> Dict[str, Any]:
    """
    Zwraca podstawowe informacje o modelu.
    """

    return {
        "parameters": count_parameters(model),
        "trainable_parameters": count_trainable_parameters(model),
    }


# ============================================================
# DATA LOADER
# ============================================================

@dataclass
class DataLoaderConfig:
    batch_size: int = 32
    shuffle: bool = True
    num_workers: int = 0
    pin_memory: bool = True
    drop_last: bool = False


def create_dataloader(
    dataset: Dataset,
    config: Optional[DataLoaderConfig] = None,
) -> DataLoader:
    """
    Tworzy DataLoader na podstawie konfiguracji.
    """

    if config is None:
        config = DataLoaderConfig()

    return DataLoader(
        dataset,
        batch_size=config.batch_size,
        shuffle=config.shuffle,
        num_workers=config.num_workers,
        pin_memory=config.pin_memory,
        drop_last=config.drop_last,
    )


# ============================================================
# OPTIMIZER
# ============================================================

def create_optimizer(
    model: nn.Module,
    optimizer_name: str = "adamw",
    learning_rate: float = 1e-4,
    weight_decay: float = 1e-4,
) -> Optimizer:
    """
    Tworzy optimizer.

    Obsługiwane:
        adam
        adamw
        sgd
    """

    name = optimizer_name.lower()

    parameters = [
        parameter
        for parameter in model.parameters()
        if parameter.requires_grad
    ]

    if name == "adam":
        return torch.optim.Adam(
            parameters,
            lr=learning_rate,
            weight_decay=weight_decay,
        )

    if name == "adamw":
        return torch.optim.AdamW(
            parameters,
            lr=learning_rate,
            weight_decay=weight_decay,
        )

    if name == "sgd":
        return torch.optim.SGD(
            parameters,
            lr=learning_rate,
            momentum=0.9,
            weight_decay=weight_decay,
        )

    raise ValueError(
        f"Unsupported optimizer: {optimizer_name}"
    )


# ============================================================
# SCHEDULER
# ============================================================

def create_scheduler(
    optimizer: Optimizer,
    scheduler_name: str = "plateau",
    epochs: int = 50,
    step_size: int = 10,
    gamma: float = 0.1,
    patience: int = 5,
):
    """
    Tworzy scheduler learning rate.

    Obsługiwane:
        plateau
        cosine
        step
        none
    """

    name = scheduler_name.lower()

    if name == "none":
        return None

    if name == "plateau":
        return ReduceLROnPlateau(
            optimizer,
            mode="min",
            factor=0.5,
            patience=patience,
        )

    if name == "cosine":
        return CosineAnnealingLR(
            optimizer,
            T_max=max(epochs, 1),
        )

    if name == "step":
        return StepLR(
            optimizer,
            step_size=step_size,
            gamma=gamma,
        )

    raise ValueError(
        f"Unsupported scheduler: {scheduler_name}"
    )


# ============================================================
# MIXED PRECISION
# ============================================================

def create_grad_scaler(
    device: torch.device,
    enabled: bool = True,
):
    """
    Tworzy GradScaler dla CUDA.

    Na CPU/MPS mixed precision jest automatycznie wyłączane.
    """

    use_scaler = (
        enabled
        and device.type == "cuda"
    )

    if not use_scaler:
        return None

    return torch.cuda.amp.GradScaler(enabled=True)


# ============================================================
# BATCH PARSING
# ============================================================

def unpack_batch(
    batch: Any,
) -> Tuple[Any, Any]:
    """
    Próbuje zunifikować format batcha.

    Obsługiwane formaty:

        (inputs, targets)

        {
            "inputs": ...,
            "targets": ...
        }

        {
            "x": ...,
            "y": ...
        }

    """

    if isinstance(batch, Mapping):
        if "inputs" in batch and "targets" in batch:
            return batch["inputs"], batch["targets"]

        if "x" in batch and "y" in batch:
            return batch["x"], batch["y"]

        raise KeyError(
            "Batch dictionary must contain "
            "'inputs'/'targets' or 'x'/'y'."
        )

    if isinstance(batch, (tuple, list)):
        if len(batch) < 2:
            raise ValueError(
                "Batch must contain inputs and targets."
            )

        return batch[0], batch[1]

    raise TypeError(
        f"Unsupported batch type: {type(batch)}"
    )


def move_to_device(
    value: Any,
    device: torch.device,
) -> Any:
    """
    Rekurencyjnie przenosi dane na urządzenie.
    """

    if torch.is_tensor(value):
        return value.to(
            device,
            non_blocking=True,
        )

    if isinstance(value, Mapping):
        return {
            key: move_to_device(item, device)
            for key, item in value.items()
        }

    if isinstance(value, tuple):
        return tuple(
            move_to_device(item, device)
            for item in value
        )

    if isinstance(value, list):
        return [
            move_to_device(item, device)
            for item in value
        ]

    return value


# ============================================================
# LOSS
# ============================================================

def create_classification_loss(
    num_classes: int,
    class_weights: Optional[Sequence[float]] = None,
    label_smoothing: float = 0.0,
) -> nn.Module:
    """
    Tworzy CrossEntropyLoss dla klasyfikacji wieloklasowej.
    """

    weight = None

    if class_weights is not None:
        weight = torch.tensor(
            class_weights,
            dtype=torch.float32,
        )

        if len(weight) != num_classes:
            raise ValueError(
                "Number of class weights must match "
                "num_classes."
            )

    return nn.CrossEntropyLoss(
        weight=weight,
        label_smoothing=label_smoothing,
    )


def create_binary_loss(
    pos_weight: Optional[float] = None,
) -> nn.Module:
    """
    Loss dla binarnej klasyfikacji z jednym logitem.
    """

    weight = None

    if pos_weight is not None:
        weight = torch.tensor(
            [pos_weight],
            dtype=torch.float32,
        )

    return nn.BCEWithLogitsLoss(
        pos_weight=weight,
    )


def create_regression_loss(
    loss_name: str = "mse",
) -> nn.Module:
    """
    Loss dla regresji.
    """

    name = loss_name.lower()

    if name == "mse":
        return nn.MSELoss()

    if name == "mae":
        return nn.L1Loss()

    if name == "huber":
        return nn.HuberLoss()

    raise ValueError(
        f"Unsupported regression loss: {loss_name}"
    )


# ============================================================
# METRICS
# ============================================================

def classification_accuracy(
    logits: torch.Tensor,
    targets: torch.Tensor,
) -> float:
    """
    Accuracy dla klasyfikacji wieloklasowej.
    """

    predictions = torch.argmax(
        logits,
        dim=1,
    )

    correct = (
        predictions == targets
    ).sum().item()

    total = targets.numel()

    if total == 0:
        return 0.0

    return correct / total


def binary_accuracy(
    logits: torch.Tensor,
    targets: torch.Tensor,
    threshold: float = 0.5,
) -> float:
    """
    Accuracy dla binarnej klasyfikacji.
    """

    probabilities = torch.sigmoid(logits)

    predictions = (
        probabilities >= threshold
    ).long()

    targets = targets.long()

    correct = (
        predictions == targets
    ).sum().item()

    total = targets.numel()

    if total == 0:
        return 0.0

    return correct / total


def regression_metrics(
    predictions: torch.Tensor,
    targets: torch.Tensor,
) -> Dict[str, float]:
    """
    Podstawowe metryki regresji.
    """

    predictions = predictions.detach().float()
    targets = targets.detach().float()

    mse = torch.mean(
        (predictions - targets) ** 2
    ).item()

    mae = torch.mean(
        torch.abs(predictions - targets)
    ).item()

    rmse = math.sqrt(mse)

    return {
        "mse": mse,
        "mae": mae,
        "rmse": rmse,
    }


# ============================================================
# TRAINING RESULT
# ============================================================

@dataclass
class EpochResult:
    epoch: int
    train_loss: float
    validation_loss: Optional[float] = None
    train_metric: Optional[float] = None
    validation_metric: Optional[float] = None
    learning_rate: Optional[float] = None


# ============================================================
# EARLY STOPPING
# ============================================================

@dataclass
class EarlyStopping:
    patience: int = 10
    min_delta: float = 0.0
    mode: str = "min"

    best_value: Optional[float] = None
    counter: int = 0
    stopped: bool = False

    def __post_init__(self):
        self.mode = self.mode.lower()

        if self.mode not in {"min", "max"}:
            raise ValueError(
                "EarlyStopping mode must be 'min' or 'max'."
            )

    def _is_improvement(
        self,
        value: float,
    ) -> bool:

        if self.best_value is None:
            return True

        if self.mode == "min":
            return value < (
                self.best_value - self.min_delta
            )

        return value > (
            self.best_value + self.min_delta
        )

    def step(
        self,
        value: float,
    ) -> bool:

        if self._is_improvement(value):
            self.best_value = value
            self.counter = 0
            return False

        self.counter += 1

        if self.counter >= self.patience:
            self.stopped = True

        return self.stopped


# ============================================================
# CHECKPOINT
# ============================================================

def save_checkpoint(
    path: str | Path,
    model: nn.Module,
    optimizer: Optional[Optimizer] = None,
    scheduler: Any = None,
    epoch: Optional[int] = None,
    best_metric: Optional[float] = None,
    config: Optional[Dict[str, Any]] = None,
    extra: Optional[Dict[str, Any]] = None,
) -> None:
    """
    Zapisuje pełny checkpoint treningowy.
    """

    path = Path(path)

    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    checkpoint = {
        "model_state_dict": model.state_dict(),
    }

    if optimizer is not None:
        checkpoint[
            "optimizer_state_dict"
        ] = optimizer.state_dict()

    if scheduler is not None:
        checkpoint[
            "scheduler_state_dict"
        ] = scheduler.state_dict()

    if epoch is not None:
        checkpoint["epoch"] = epoch

    if best_metric is not None:
        checkpoint["best_metric"] = best_metric

    if config is not None:
        checkpoint["config"] = config

    if extra is not None:
        checkpoint["extra"] = extra

    torch.save(
        checkpoint,
        path,
    )

    LOGGER.info(
        "Checkpoint saved: %s",
        path,
    )


def load_checkpoint(
    path: str | Path,
    model: nn.Module,
    optimizer: Optional[Optimizer] = None,
    scheduler: Any = None,
    device: str | torch.device = "cpu",
    strict: bool = True,
) -> Dict[str, Any]:
    """
    Wczytuje checkpoint modelu.
    """

    path = Path(path)

    if not path.exists():
        raise FileNotFoundError(
            f"Checkpoint not found: {path}"
        )

    checkpoint = torch.load(
        path,
        map_location=device,
    )

    model.load_state_dict(
        checkpoint["model_state_dict"],
        strict=strict,
    )

    if (
        optimizer is not None
        and "optimizer_state_dict" in checkpoint
    ):
        optimizer.load_state_dict(
            checkpoint["optimizer_state_dict"]
        )

    if (
        scheduler is not None
        and "scheduler_state_dict" in checkpoint
    ):
        scheduler.load_state_dict(
            checkpoint["scheduler_state_dict"]
        )

    LOGGER.info(
        "Checkpoint loaded: %s",
        path,
    )

    return checkpoint


# ============================================================
# HISTORY
# ============================================================

def save_training_history(
    history: Sequence[EpochResult],
    path: str | Path,
) -> None:
    """
    Zapisuje historię treningu do JSON.
    """

    path = Path(path)

    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    data = [
        asdict(result)
        for result in history
    ]

    with path.open(
        "w",
        encoding="utf-8",
    ) as file:

        json.dump(
            data,
            file,
            indent=2,
        )


# ============================================================
# ONE EPOCH - CLASSIFICATION
# ============================================================

def train_classification_epoch(
    model: nn.Module,
    dataloader: DataLoader,
    criterion: nn.Module,
    optimizer: Optimizer,
    device: torch.device,
    scaler=None,
    binary: bool = False,
    max_grad_norm: Optional[float] = 1.0,
) -> Tuple[float, float]:
    """
    Wykonuje jedną epokę treningową dla klasyfikacji.
    """

    model.train()

    total_loss = 0.0
    total_samples = 0
    total_correct = 0

    use_amp = (
        scaler is not None
        and device.type == "cuda"
    )

    for batch in dataloader:

        inputs, targets = unpack_batch(batch)

        inputs = move_to_device(
            inputs,
            device,
        )

        targets = move_to_device(
            targets,
            device,
        )

        optimizer.zero_grad(
            set_to_none=True
        )

        if use_amp:

            with torch.cuda.amp.autocast():

                logits = model(inputs)

                if binary:
                    targets_float = (
                        targets.float()
                    )

                    logits = logits.squeeze(-1)

                    loss = criterion(
                        logits,
                        targets_float,
                    )

                else:
                    targets_long = (
                        targets.long()
                    )

                    loss = criterion(
                        logits,
                        targets_long,
                    )

            scaler.scale(loss).backward()

            if max_grad_norm is not None:

                scaler.unscale_(
                    optimizer
                )

                torch.nn.utils.clip_grad_norm_(
                    model.parameters(),
                    max_grad_norm,
                )

            scaler.step(optimizer)
            scaler.update()

        else:

            logits = model(inputs)

            if binary:

                targets_float = (
                    targets.float()
                )

                logits = logits.squeeze(-1)

                loss = criterion(
                    logits,
                    targets_float,
                )

            else:

                targets_long = (
                    targets.long()
                )

                loss = criterion(
                    logits,
                    targets_long,
                )

            loss.backward()

            if max_grad_norm is not None:

                torch.nn.utils.clip_grad_norm_(
                    model.parameters(),
                    max_grad_norm,
                )

            optimizer.step()

        batch_size = targets.shape[0]

        total_loss += (
            loss.detach().item()
            * batch_size
        )

        total_samples += batch_size

        if binary:

            predictions = (
                torch.sigmoid(logits)
                >= 0.5
            ).long()

            target_labels = (
                targets.long()
            )

        else:

            predictions = torch.argmax(
                logits,
                dim=1,
            )

            target_labels = (
                targets.long()
            )

        total_correct += (
            predictions == target_labels
        ).sum().item()

    if total_samples == 0:
        return 0.0, 0.0

    epoch_loss = (
        total_loss / total_samples
    )

    epoch_accuracy = (
        total_correct / total_samples
    )

    return (
        epoch_loss,
        epoch_accuracy,
    )


# ============================================================
# ONE EPOCH - VALIDATION
# ============================================================

@torch.no_grad()
def validate_classification_epoch(
    model: nn.Module,
    dataloader: DataLoader,
    criterion: nn.Module,
    device: torch.device,
    binary: bool = False,
) -> Tuple[float, float]:
    """
    Waliduje model klasyfikacyjny.
    """

    model.eval()

    total_loss = 0.0
    total_samples = 0
    total_correct = 0

    for batch in dataloader:

        inputs, targets = unpack_batch(batch)

        inputs = move_to_device(
            inputs,
            device,
        )

        targets = move_to_device(
            targets,
            device,
        )

        logits = model(inputs)

        if binary:

            logits = logits.squeeze(-1)

            loss = criterion(
                logits,
                targets.float(),
            )

            predictions = (
                torch.sigmoid(logits)
                >= 0.5
            ).long()

        else:

            loss = criterion(
                logits,
                targets.long(),
            )

            predictions = torch.argmax(
                logits,
                dim=1,
            )

        batch_size = targets.shape[0]

        total_loss += (
            loss.item()
            * batch_size
        )

        total_samples += batch_size

        total_correct += (
            predictions
            == targets.long()
        ).sum().item()

    if total_samples == 0:
        return 0.0, 0.0

    return (
        total_loss / total_samples,
        total_correct / total_samples,
    )


# ============================================================
# ONE EPOCH - REGRESSION
# ============================================================

def train_regression_epoch(
    model: nn.Module,
    dataloader: DataLoader,
    criterion: nn.Module,
    optimizer: Optimizer,
    device: torch.device,
    scaler=None,
    max_grad_norm: Optional[float] = 1.0,
) -> Tuple[float, float]:
    """
    Jedna epoka treningowa regresji.

    Zwraca:
        loss
        MAE
    """

    model.train()

    total_loss = 0.0
    total_abs_error = 0.0
    total_samples = 0

    use_amp = (
        scaler is not None
        and device.type == "cuda"
    )

    for batch in dataloader:

        inputs, targets = unpack_batch(batch)

        inputs = move_to_device(
            inputs,
            device,
        )

        targets = move_to_device(
            targets,
            device,
        )

        optimizer.zero_grad(
            set_to_none=True
        )

        if use_amp:

            with torch.cuda.amp.autocast():

                predictions = model(inputs)

                predictions = predictions.squeeze()

                targets = targets.float()

                loss = criterion(
                    predictions,
                    targets,
                )

            scaler.scale(loss).backward()

            if max_grad_norm is not None:

                scaler.unscale_(
                    optimizer
                )

                torch.nn.utils.clip_grad_norm_(
                    model.parameters(),
                    max_grad_norm,
                )

            scaler.step(optimizer)
            scaler.update()

        else:

            predictions = model(inputs)

            predictions = predictions.squeeze()

            targets = targets.float()

            loss = criterion(
                predictions,
                targets,
            )

            loss.backward()

            if max_grad_norm is not None:

                torch.nn.utils.clip_grad_norm_(
                    model.parameters(),
                    max_grad_norm,
                )

            optimizer.step()

        batch_size = targets.shape[0]

        total_loss += (
            loss.detach().item()
            * batch_size
        )

        total_abs_error += (
            torch.abs(
                predictions.detach()
                - targets
            ).sum().item()
        )

        total_samples += batch_size

    if total_samples == 0:
        return 0.0, 0.0

    return (
        total_loss / total_samples,
        total_abs_error / total_samples,
    )


# ============================================================
# VALIDATION - REGRESSION
# ============================================================

@torch.no_grad()
def validate_regression_epoch(
    model: nn.Module,
    dataloader: DataLoader,
    criterion: nn.Module,
    device: torch.device,
) -> Tuple[float, float]:
    """
    Walidacja regresji.
    """

    model.eval()

    total_loss = 0.0
    total_abs_error = 0.0
    total_samples = 0

    for batch in dataloader:

        inputs, targets = unpack_batch(batch)

        inputs = move_to_device(
            inputs,
            device,
        )

        targets = move_to_device(
            targets,
            device,
        )

        predictions = model(inputs)

        predictions = predictions.squeeze()

        targets = targets.float()

        loss = criterion(
            predictions,
            targets,
        )

        batch_size = targets.shape[0]

        total_loss += (
            loss.item()
            * batch_size
        )

        total_abs_error += (
            torch.abs(
                predictions
                - targets
            ).sum().item()
        )

        total_samples += batch_size

    if total_samples == 0:
        return 0.0, 0.0

    return (
        total_loss / total_samples,
        total_abs_error / total_samples,
    )


# ============================================================
# LEARNING RATE
# ============================================================

def get_learning_rate(
    optimizer: Optimizer,
) -> float:
    """
    Pobiera aktualny learning rate.
    """

    return float(
        optimizer.param_groups[0]["lr"]
    )


# ============================================================
# SCHEDULER STEP
# ============================================================

def step_scheduler(
    scheduler: Any,
    validation_loss: Optional[float] = None,
) -> None:
    """
    Wykonuje krok schedulera.

    ReduceLROnPlateau wymaga validation_loss.
    Pozostałe schedulery nie.
    """

    if scheduler is None:
        return

    if isinstance(
        scheduler,
        ReduceLROnPlateau,
    ):

        if validation_loss is None:
            raise ValueError(
                "validation_loss is required "
                "for ReduceLROnPlateau."
            )

        scheduler.step(
            validation_loss
        )

    else:

        scheduler.step()


# ============================================================
# FULL CLASSIFICATION TRAINING LOOP
# ============================================================

def fit_classifier(
    model: nn.Module,
    train_loader: DataLoader,
    validation_loader: DataLoader,
    criterion: nn.Module,
    optimizer: Optimizer,
    device: torch.device,
    epochs: int = 50,
    scheduler: Any = None,
    checkpoint_path: Optional[str | Path] = None,
    config: Optional[Dict[str, Any]] = None,
    binary: bool = False,
    patience: int = 10,
    min_delta: float = 0.0,
    scaler=None,
) -> List[EpochResult]:
    """
    Pełny trening klasyfikatora.
    """

    model.to(device)

    history: List[EpochResult] = []

    early_stopping = EarlyStopping(
        patience=patience,
        min_delta=min_delta,
        mode="min",
    )

    best_validation_loss = float("inf")

    for epoch in range(1, epochs + 1):

        train_loss, train_accuracy = (
            train_classification_epoch(
                model=model,
                dataloader=train_loader,
                criterion=criterion,
                optimizer=optimizer,
                device=device,
                scaler=scaler,
                binary=binary,
            )
        )

        validation_loss, validation_accuracy = (
            validate_classification_epoch(
                model=model,
                dataloader=validation_loader,
                criterion=criterion,
                device=device,
                binary=binary,
            )
        )

        step_scheduler(
            scheduler,
            validation_loss,
        )

        learning_rate = get_learning_rate(
            optimizer
        )

        result = EpochResult(
            epoch=epoch,
            train_loss=train_loss,
            validation_loss=validation_loss,
            train_metric=train_accuracy,
            validation_metric=validation_accuracy,
            learning_rate=learning_rate,
        )

        history.append(result)

        LOGGER.info(
            "Epoch %d/%d | "
            "train_loss=%.5f | "
            "val_loss=%.5f | "
            "train_acc=%.4f | "
            "val_acc=%.4f | "
            "lr=%.2e",
            epoch,
            epochs,
            train_loss,
            validation_loss,
            train_accuracy,
            validation_accuracy,
            learning_rate,
        )

        if validation_loss < best_validation_loss:

            best_validation_loss = (
                validation_loss
            )

            if checkpoint_path is not None:

                save_checkpoint(
                    path=checkpoint_path,
                    model=model,
                    optimizer=optimizer,
                    scheduler=scheduler,
                    epoch=epoch,
                    best_metric=validation_loss,
                    config=config,
                )

        if early_stopping.step(
            validation_loss
        ):

            LOGGER.info(
                "Early stopping at epoch %d.",
                epoch,
            )

            break

    return history


# ============================================================
# FULL REGRESSION TRAINING LOOP
# ============================================================

def fit_regressor(
    model: nn.Module,
    train_loader: DataLoader,
    validation_loader: DataLoader,
    criterion: nn.Module,
    optimizer: Optimizer,
    device: torch.device,
    epochs: int = 50,
    scheduler: Any = None,
    checkpoint_path: Optional[str | Path] = None,
    config: Optional[Dict[str, Any]] = None,
    patience: int = 10,
    min_delta: float = 0.0,
    scaler=None,
) -> List[EpochResult]:
    """
    Pełny trening modelu regresyjnego.
    """

    model.to(device)

    history: List[EpochResult] = []

    early_stopping = EarlyStopping(
        patience=patience,
        min_delta=min_delta,
        mode="min",
    )

    best_validation_loss = float("inf")

    for epoch in range(1, epochs + 1):

        train_loss, train_mae = (
            train_regression_epoch(
                model=model,
                dataloader=train_loader,
                criterion=criterion,
                optimizer=optimizer,
                device=device,
                scaler=scaler,
            )
        )

        validation_loss, validation_mae = (
            validate_regression_epoch(
                model=model,
                dataloader=validation_loader,
                criterion=criterion,
                device=device,
            )
        )

        step_scheduler(
            scheduler,
            validation_loss,
        )

        learning_rate = get_learning_rate(
            optimizer
        )

        result = EpochResult(
            epoch=epoch,
            train_loss=train_loss,
            validation_loss=validation_loss,
            train_metric=train_mae,
            validation_metric=validation_mae,
            learning_rate=learning_rate,
        )

        history.append(result)

        LOGGER.info(
            "Epoch %d/%d | "
            "train_loss=%.5f | "
            "val_loss=%.5f | "
            "train_mae=%.5f | "
            "val_mae=%.5f | "
            "lr=%.2e",
            epoch,
            epochs,
            train_loss,
            validation_loss,
            train_mae,
            validation_mae,
            learning_rate,
        )

        if validation_loss < best_validation_loss:

            best_validation_loss = (
                validation_loss
            )

            if checkpoint_path is not None:

                save_checkpoint(
                    path=checkpoint_path,
                    model=model,
                    optimizer=optimizer,
                    scheduler=scheduler,
                    epoch=epoch,
                    best_metric=validation_loss,
                    config=config,
                )

        if early_stopping.step(
            validation_loss
        ):

            LOGGER.info(
                "Early stopping at epoch %d.",
                epoch,
            )

            break

    return history


# ============================================================
# WEIGHT INITIALIZATION
# ============================================================

def initialize_weights(
    module: nn.Module,
) -> None:
    """
    Standardowa inicjalizacja warstw Linear i Conv.
    """

    if isinstance(
        module,
        (nn.Linear, nn.Conv1d, nn.Conv2d, nn.Conv3d),
    ):

        nn.init.kaiming_normal_(
            module.weight,
            nonlinearity="relu",
        )

        if module.bias is not None:
            nn.init.zeros_(
                module.bias
            )

    elif isinstance(
        module,
        (nn.BatchNorm1d, nn.BatchNorm2d, nn.BatchNorm3d),
    ):

        nn.init.ones_(
            module.weight
        )

        nn.init.zeros_(
            module.bias
        )


# ============================================================
# FREEZE / UNFREEZE
# ============================================================

def freeze_model(
    model: nn.Module,
) -> None:
    """
    Zamraża wszystkie parametry modelu.
    """

    for parameter in model.parameters():
        parameter.requires_grad = False


def unfreeze_model(
    model: nn.Module,
) -> None:
    """
    Odblokowuje wszystkie parametry modelu.
    """

    for parameter in model.parameters():
        parameter.requires_grad = True


def freeze_except(
    model: nn.Module,
    trainable_prefixes: Sequence[str],
) -> None:
    """
    Zamraża model poza wskazanymi nazwami parametrów.

    Przydatne np. przy fine-tuningu.
    """

    for name, parameter in model.named_parameters():

        parameter.requires_grad = any(
            name.startswith(prefix)
            for prefix in trainable_prefixes
        )


# ============================================================
# CHECKPOINT DIRECTORY
# ============================================================

def ensure_checkpoint_directory(
    root: str | Path,
    model_name: str,
) -> Path:
    """
    Tworzy katalog:

        root/model_name/

    i zwraca jego ścieżkę.
    """

    directory = (
        Path(root)
        / model_name
    )

    directory.mkdir(
        parents=True,
        exist_ok=True,
    )

    return directory


# ============================================================
# CONFIG SERIALIZATION
# ============================================================

def save_config(
    config: Dict[str, Any],
    path: str | Path,
) -> None:
    """
    Zapisuje konfigurację treningu.
    """

    path = Path(path)

    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with path.open(
        "w",
        encoding="utf-8",
    ) as file:

        json.dump(
            config,
            file,
            indent=2,
            ensure_ascii=False,
        )


# ============================================================
# EXPERIMENT DIRECTORY
# ============================================================

def create_experiment_directory(
    root: str | Path,
    experiment_name: str,
) -> Path:
    """
    Tworzy katalog eksperymentu.
    """

    directory = (
        Path(root)
        / experiment_name
    )

    directory.mkdir(
        parents=True,
        exist_ok=True,
    )

    return directory


# ============================================================
# TRAINING SUMMARY
# ============================================================

def print_training_summary(
    model: nn.Module,
    device: torch.device,
    config: Optional[Dict[str, Any]] = None,
) -> None:
    """
    Wyświetla krótkie podsumowanie treningu/modelu.
    """

    print("\n" + "=" * 60)
    print("TRAINING SUMMARY")
    print("=" * 60)

    print(
        f"Device: {device}"
    )

    print(
        f"Parameters: "
        f"{count_parameters(model):,}"
    )

    print(
        f"Trainable parameters: "
        f"{count_trainable_parameters(model):,}"
    )

    if config is not None:

        print(
            "\nConfiguration:"
        )

        for key, value in config.items():

            print(
                f"  {key}: {value}"
            )

    print("=" * 60)


# ============================================================
# SIMPLE FEATURE DATASET
# ============================================================

class TensorDatasetWrapper(Dataset):
    """
    Prosty Dataset dla gotowych tensorów.

    Przydatny do treningu modeli na embeddingach
    wygenerowanych wcześniej przez DINOv2, Scanpy itd.

    Przykład:

        dataset = TensorDatasetWrapper(
            features,
            labels
        )
    """

    def __init__(
        self,
        features: torch.Tensor,
        targets: torch.Tensor,
    ):
        if len(features) != len(targets):
            raise ValueError(
                "Features and targets must have "
                "the same number of samples."
            )

        self.features = features
        self.targets = targets

    def __len__(self) -> int:
        return len(self.features)

    def __getitem__(
        self,
        index: int,
    ):
        return (
            self.features[index],
            self.targets[index],
        )


# ============================================================
# DATASET SPLIT
# ============================================================

def split_dataset(
    dataset: Dataset,
    train_ratio: float = 0.8,
    validation_ratio: float = 0.1,
    test_ratio: float = 0.1,
    seed: int = 42,
) -> Tuple[Dataset, Dataset, Dataset]:
    """
    Dzieli dataset na train/validation/test.

    Uwaga:
    W przypadku danych medycznych docelowo należy
    stosować split na poziomie pacjenta,
    a nie losowo na poziomie pojedynczych obrazów.
    """

    total = (
        train_ratio
        + validation_ratio
        + test_ratio
    )

    if not math.isclose(
        total,
        1.0,
        rel_tol=1e-6,
    ):
        raise ValueError(
            "train_ratio + validation_ratio + "
            "test_ratio must equal 1."
        )

    generator = torch.Generator()

    generator.manual_seed(seed)

    train_size = int(
        len(dataset)
        * train_ratio
    )

    validation_size = int(
        len(dataset)
        * validation_ratio
    )

    test_size = (
        len(dataset)
        - train_size
        - validation_size
    )

    return torch.utils.data.random_split(
        dataset,
        [
            train_size,
            validation_size,
            test_size,
        ],
        generator=generator,
    )


# ============================================================
# MAIN TEST
# ============================================================

if __name__ == "__main__":

    logger = setup_logger()

    set_seed(42)

    device = get_device()

    logger.info(
        "Training utilities initialized."
    )

    logger.info(
        "Device: %s",
        device,
    )

    print(
        "\ntrain_utils.py is ready."
    )