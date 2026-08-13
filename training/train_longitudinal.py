"""
train_longitudinal.py

Training script for the longitudinal model.

Purpose
-------
Train a model that learns how multimodal biological features change over time.

Expected temporal structure:

    T0 -> T1 -> T2 -> T3

Each time point may contain features originating from:

    - clinical / metadata information
    - skin images
    - WSI / pathology
    - cellular analysis
    - RNA / transcriptomics
    - hand morphology
    - fused multimodal embeddings

The training script is intentionally modular so that it can work with
precomputed embeddings instead of loading raw images, WSI or RNA data
directly.

Typical input:
    data/processed/embeddings/longitudinal/

Example:
    sample_001/
        T0.npy
        T1.npy
        T2.npy
        T3.npy

or:

    sample_001/
        T0.pt
        T1.pt
        T2.pt
        T3.pt

The exact feature generation should be handled by the pipeline layer.
This script is responsible primarily for training.
"""

from __future__ import annotations

import argparse
import json
import random
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple

import numpy as np
import torch
import torch.nn as nn
from torch.utils.data import DataLoader, Dataset, random_split


# -------------------------------------------------------------------------
# Reproducibility
# -------------------------------------------------------------------------

def set_seed(seed: int = 42) -> None:
    """
    Set random seeds for reproducible training.
    """

    random.seed(seed)
    np.random.seed(seed)

    torch.manual_seed(seed)

    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)

    # Reproducibility can reduce performance slightly.
    torch.backends.cudnn.deterministic = True
    torch.backends.cudnn.benchmark = False


# -------------------------------------------------------------------------
# Configuration
# -------------------------------------------------------------------------

@dataclass
class TrainingConfig:
    """
    Configuration for longitudinal training.
    """

    input_dim: int = 768
    hidden_dim: int = 512

    num_timepoints: int = 4

    output_dim: int = 1

    dropout: float = 0.2

    batch_size: int = 8
    epochs: int = 50

    learning_rate: float = 1e-4
    weight_decay: float = 1e-5

    validation_split: float = 0.2

    seed: int = 42

    device: str = "cuda"

    output_dir: str = "outputs/longitudinal"

    checkpoint_name: str = "longitudinal_model.pt"


# -------------------------------------------------------------------------
# Device
# -------------------------------------------------------------------------

def get_device(requested_device: str) -> torch.device:
    """
    Select training device.
    """

    if requested_device == "cuda" and torch.cuda.is_available():
        return torch.device("cuda")

    if requested_device == "mps" and torch.backends.mps.is_available():
        return torch.device("mps")

    return torch.device("cpu")


# -------------------------------------------------------------------------
# Dataset
# -------------------------------------------------------------------------

class LongitudinalDataset(Dataset):
    """
    Dataset for longitudinal samples.

    Each sample consists of a sequence of feature vectors:

        T0
        T1
        T2
        T3

    Shape:

        [num_timepoints, input_dim]

    Target:

        scalar value

    The target can represent, for example:

        - biological age
        - progression score
        - future risk
        - longitudinal abnormality score

    The exact target definition should be decided by the research
    protocol and not hard-coded into the data loader.
    """

    def __init__(
        self,
        features: np.ndarray,
        targets: np.ndarray,
    ) -> None:

        if features.ndim != 3:
            raise ValueError(
                "features must have shape "
                "[num_samples, num_timepoints, input_dim]"
            )

        if targets.ndim == 1:
            targets = targets.reshape(-1, 1)

        if len(features) != len(targets):
            raise ValueError(
                "Number of feature samples and targets must match."
            )

        self.features = torch.tensor(
            features,
            dtype=torch.float32,
        )

        self.targets = torch.tensor(
            targets,
            dtype=torch.float32,
        )

    def __len__(self) -> int:
        return len(self.features)

    def __getitem__(
        self,
        index: int,
    ) -> Tuple[torch.Tensor, torch.Tensor]:

        return (
            self.features[index],
            self.targets[index],
        )


# -------------------------------------------------------------------------
# Data loading
# -------------------------------------------------------------------------

def load_numpy_dataset(
    features_path: str,
    targets_path: str,
) -> LongitudinalDataset:
    """
    Load longitudinal features and targets from .npy files.

    Expected feature shape:

        [N, T, D]

    Example:

        [100, 4, 768]

    Expected target shape:

        [N]

    or:

        [N, 1]
    """

    features = np.load(features_path)
    targets = np.load(targets_path)

    return LongitudinalDataset(
        features=features,
        targets=targets,
    )


# -------------------------------------------------------------------------
# Model import
# -------------------------------------------------------------------------

def build_model(config: TrainingConfig) -> nn.Module:
    """
    Import and construct the longitudinal model.

    The function first tries the project's longitudinal_model.py.

    This allows the training script to remain compatible with the
    architecture defined in:

        models/longitudinal_model.py
    """

    try:

        from models.longitudinal_model import LongitudinalModel

    except ImportError as exc:

        raise ImportError(
            "Could not import LongitudinalModel from "
            "models/longitudinal_model.py. "
            "Make sure you run the script from the project root."
        ) from exc

    model = LongitudinalModel(
        input_dim=config.input_dim,
        hidden_dim=config.hidden_dim,
        num_timepoints=config.num_timepoints,
        output_dim=config.output_dim,
        dropout=config.dropout,
    )

    return model


# -------------------------------------------------------------------------
# Metrics
# -------------------------------------------------------------------------

def mean_absolute_error(
    predictions: torch.Tensor,
    targets: torch.Tensor,
) -> float:

    return torch.mean(
        torch.abs(predictions - targets)
    ).item()


def mean_squared_error(
    predictions: torch.Tensor,
    targets: torch.Tensor,
) -> float:

    return torch.mean(
        (predictions - targets) ** 2
    ).item()


def root_mean_squared_error(
    predictions: torch.Tensor,
    targets: torch.Tensor,
) -> float:

    mse = mean_squared_error(
        predictions,
        targets,
    )

    return float(np.sqrt(mse))


# -------------------------------------------------------------------------
# Training epoch
# -------------------------------------------------------------------------

def train_one_epoch(
    model: nn.Module,
    loader: DataLoader,
    optimizer: torch.optim.Optimizer,
    criterion: nn.Module,
    device: torch.device,
) -> Dict[str, float]:

    model.train()

    total_loss = 0.0

    all_predictions: List[torch.Tensor] = []
    all_targets: List[torch.Tensor] = []

    for features, targets in loader:

        features = features.to(device)
        targets = targets.to(device)

        optimizer.zero_grad()

        predictions = model(features)

        # Some model implementations return
        # dictionaries or tuples.
        if isinstance(predictions, dict):

            if "prediction" in predictions:
                predictions = predictions["prediction"]

            elif "output" in predictions:
                predictions = predictions["output"]

            else:
                raise ValueError(
                    "Model dictionary output does not contain "
                    "'prediction' or 'output'."
                )

        elif isinstance(predictions, tuple):

            predictions = predictions[0]

        loss = criterion(
            predictions,
            targets,
        )

        loss.backward()

        torch.nn.utils.clip_grad_norm_(
            model.parameters(),
            max_norm=1.0,
        )

        optimizer.step()

        total_loss += loss.item() * features.size(0)

        all_predictions.append(
            predictions.detach().cpu()
        )

        all_targets.append(
            targets.detach().cpu()
        )

    predictions = torch.cat(
        all_predictions,
        dim=0,
    )

    targets = torch.cat(
        all_targets,
        dim=0,
    )

    dataset_size = len(loader.dataset)

    return {
        "loss": total_loss / dataset_size,
        "mae": mean_absolute_error(
            predictions,
            targets,
        ),
        "rmse": root_mean_squared_error(
            predictions,
            targets,
        ),
    }


# -------------------------------------------------------------------------
# Validation epoch
# -------------------------------------------------------------------------

@torch.no_grad()
def validate_one_epoch(
    model: nn.Module,
    loader: DataLoader,
    criterion: nn.Module,
    device: torch.device,
) -> Dict[str, float]:

    model.eval()

    total_loss = 0.0

    all_predictions: List[torch.Tensor] = []
    all_targets: List[torch.Tensor] = []

    for features, targets in loader:

        features = features.to(device)
        targets = targets.to(device)

        predictions = model(features)

        if isinstance(predictions, dict):

            if "prediction" in predictions:
                predictions = predictions["prediction"]

            elif "output" in predictions:
                predictions = predictions["output"]

            else:
                raise ValueError(
                    "Model dictionary output does not contain "
                    "'prediction' or 'output'."
                )

        elif isinstance(predictions, tuple):

            predictions = predictions[0]

        loss = criterion(
            predictions,
            targets,
        )

        total_loss += loss.item() * features.size(0)

        all_predictions.append(
            predictions.cpu()
        )

        all_targets.append(
            targets.cpu()
        )

    predictions = torch.cat(
        all_predictions,
        dim=0,
    )

    targets = torch.cat(
        all_targets,
        dim=0,
    )

    dataset_size = len(loader.dataset)

    return {
        "loss": total_loss / dataset_size,
        "mae": mean_absolute_error(
            predictions,
            targets,
        ),
        "rmse": root_mean_squared_error(
            predictions,
            targets,
        ),
    }


# -------------------------------------------------------------------------
# Parameter counting
# -------------------------------------------------------------------------

def count_parameters(
    model: nn.Module,
) -> Tuple[int, int]:

    total = sum(
        parameter.numel()
        for parameter in model.parameters()
    )

    trainable = sum(
        parameter.numel()
        for parameter in model.parameters()
        if parameter.requires_grad
    )

    return total, trainable


# -------------------------------------------------------------------------
# Checkpoint
# -------------------------------------------------------------------------

def save_checkpoint(
    model: nn.Module,
    optimizer: torch.optim.Optimizer,
    epoch: int,
    metrics: Dict[str, float],
    config: TrainingConfig,
    path: Path,
) -> None:

    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    checkpoint = {
        "epoch": epoch,
        "model_state_dict": model.state_dict(),
        "optimizer_state_dict": optimizer.state_dict(),
        "metrics": metrics,
        "config": asdict(config),
    }

    torch.save(
        checkpoint,
        path,
    )


# -------------------------------------------------------------------------
# Training
# -------------------------------------------------------------------------

def train(
    model: nn.Module,
    train_loader: DataLoader,
    val_loader: DataLoader,
    config: TrainingConfig,
    device: torch.device,
) -> Dict[str, List[float]]:

    criterion = nn.MSELoss()

    optimizer = torch.optim.AdamW(
        model.parameters(),
        lr=config.learning_rate,
        weight_decay=config.weight_decay,
    )

    scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(
        optimizer,
        mode="min",
        factor=0.5,
        patience=5,
    )

    output_dir = Path(config.output_dir)

    output_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    best_val_loss = float("inf")

    history: Dict[str, List[float]] = {
        "train_loss": [],
        "train_mae": [],
        "train_rmse": [],
        "val_loss": [],
        "val_mae": [],
        "val_rmse": [],
    }

    for epoch in range(1, config.epochs + 1):

        train_metrics = train_one_epoch(
            model=model,
            loader=train_loader,
            optimizer=optimizer,
            criterion=criterion,
            device=device,
        )

        val_metrics = validate_one_epoch(
            model=model,
            loader=val_loader,
            criterion=criterion,
            device=device,
        )

        scheduler.step(
            val_metrics["loss"]
        )

        history["train_loss"].append(
            train_metrics["loss"]
        )

        history["train_mae"].append(
            train_metrics["mae"]
        )

        history["train_rmse"].append(
            train_metrics["rmse"]
        )

        history["val_loss"].append(
            val_metrics["loss"]
        )

        history["val_mae"].append(
            val_metrics["mae"]
        )

        history["val_rmse"].append(
            val_metrics["rmse"]
        )

        current_lr = optimizer.param_groups[0]["lr"]

        print(
            f"Epoch {epoch:03d}/{config.epochs} | "
            f"train_loss={train_metrics['loss']:.5f} | "
            f"val_loss={val_metrics['loss']:.5f} | "
            f"train_mae={train_metrics['mae']:.5f} | "
            f"val_mae={val_metrics['mae']:.5f} | "
            f"lr={current_lr:.2e}"
        )

        if val_metrics["loss"] < best_val_loss:

            best_val_loss = val_metrics["loss"]

            checkpoint_path = (
                output_dir /
                config.checkpoint_name
            )

            save_checkpoint(
                model=model,
                optimizer=optimizer,
                epoch=epoch,
                metrics=val_metrics,
                config=config,
                path=checkpoint_path,
            )

            print(
                f"  -> saved best model: "
                f"{checkpoint_path}"
            )

    history_path = (
        output_dir /
        "training_history.json"
    )

    with open(
        history_path,
        "w",
        encoding="utf-8",
    ) as file:

        json.dump(
            history,
            file,
            indent=2,
        )

    return history


# -------------------------------------------------------------------------
# Dataset splitting
# -------------------------------------------------------------------------

def split_dataset(
    dataset: Dataset,
    validation_split: float,
    seed: int,
) -> Tuple[Dataset, Dataset]:

    if not 0.0 < validation_split < 1.0:
        raise ValueError(
            "validation_split must be between 0 and 1."
        )

    total_size = len(dataset)

    validation_size = max(
        1,
        int(total_size * validation_split),
    )

    train_size = total_size - validation_size

    if train_size < 1:
        raise ValueError(
            "Dataset is too small for the selected "
            "validation split."
        )

    generator = torch.Generator()

    generator.manual_seed(seed)

    train_dataset, validation_dataset = random_split(
        dataset,
        [train_size, validation_size],
        generator=generator,
    )

    return (
        train_dataset,
        validation_dataset,
    )


# -------------------------------------------------------------------------
# CLI
# -------------------------------------------------------------------------

def parse_args() -> argparse.Namespace:

    parser = argparse.ArgumentParser(
        description=(
            "Train the longitudinal multimodal model."
        )
    )

    parser.add_argument(
        "--features",
        type=str,
        required=True,
        help=(
            "Path to longitudinal feature .npy file. "
            "Expected shape: [N, T, D]."
        ),
    )

    parser.add_argument(
        "--targets",
        type=str,
        required=True,
        help=(
            "Path to target .npy file."
        ),
    )

    parser.add_argument(
        "--input-dim",
        type=int,
        default=768,
    )

    parser.add_argument(
        "--hidden-dim",
        type=int,
        default=512,
    )

    parser.add_argument(
        "--timepoints",
        type=int,
        default=4,
    )

    parser.add_argument(
        "--epochs",
        type=int,
        default=50,
    )

    parser.add_argument(
        "--batch-size",
        type=int,
        default=8,
    )

    parser.add_argument(
        "--learning-rate",
        type=float,
        default=1e-4,
    )

    parser.add_argument(
        "--weight-decay",
        type=float,
        default=1e-5,
    )

    parser.add_argument(
        "--dropout",
        type=float,
        default=0.2,
    )

    parser.add_argument(
        "--validation-split",
        type=float,
        default=0.2,
    )

    parser.add_argument(
        "--device",
        type=str,
        default="cuda",
        choices=[
            "cuda",
            "cpu",
            "mps",
        ],
    )

    parser.add_argument(
        "--output-dir",
        type=str,
        default="outputs/longitudinal",
    )

    parser.add_argument(
        "--seed",
        type=int,
        default=42,
    )

    return parser.parse_args()


# -------------------------------------------------------------------------
# Main
# -------------------------------------------------------------------------

def main() -> None:

    args = parse_args()

    config = TrainingConfig(
        input_dim=args.input_dim,
        hidden_dim=args.hidden_dim,
        num_timepoints=args.timepoints,
        epochs=args.epochs,
        batch_size=args.batch_size,
        learning_rate=args.learning_rate,
        weight_decay=args.weight_decay,
        dropout=args.dropout,
        validation_split=args.validation_split,
        device=args.device,
        output_dir=args.output_dir,
        seed=args.seed,
    )

    print()
    print("=" * 70)
    print("Longitudinal Model Training")
    print("=" * 70)

    print()
    print("Configuration:")

    for key, value in asdict(config).items():

        print(
            f"  {key}: {value}"
        )

    # -------------------------------------------------------------
    # Seed
    # -------------------------------------------------------------

    set_seed(
        config.seed
    )

    # -------------------------------------------------------------
    # Device
    # -------------------------------------------------------------

    device = get_device(
        config.device
    )

    print()
    print(
        f"Device: {device}"
    )

    # -------------------------------------------------------------
    # Load dataset
    # -------------------------------------------------------------

    print()
    print("Loading longitudinal dataset...")

    dataset = load_numpy_dataset(
        features_path=args.features,
        targets_path=args.targets,
    )

    print(
        f"Samples: {len(dataset)}"
    )

    print(
        f"Feature shape: "
        f"{tuple(dataset.features.shape)}"
    )

    print(
        f"Target shape: "
        f"{tuple(dataset.targets.shape)}"
    )

    # -------------------------------------------------------------
    # Dataset validation
    # -------------------------------------------------------------

    feature_shape = dataset.features.shape

    if feature_shape[1] != config.num_timepoints:

        raise ValueError(
            f"Dataset contains {feature_shape[1]} timepoints, "
            f"but config expects {config.num_timepoints}."
        )

    if feature_shape[2] != config.input_dim:

        raise ValueError(
            f"Dataset input dimension is {feature_shape[2]}, "
            f"but config expects {config.input_dim}."
        )

    # -------------------------------------------------------------
    # Split
    # -------------------------------------------------------------

    train_dataset, val_dataset = split_dataset(
        dataset=dataset,
        validation_split=config.validation_split,
        seed=config.seed,
    )

    print()
    print(
        f"Training samples: "
        f"{len(train_dataset)}"
    )

    print(
        f"Validation samples: "
        f"{len(val_dataset)}"
    )

    # -------------------------------------------------------------
    # Data loaders
    # -------------------------------------------------------------

    train_loader = DataLoader(
        train_dataset,
        batch_size=config.batch_size,
        shuffle=True,
        num_workers=0,
        pin_memory=(
            device.type == "cuda"
        ),
    )

    val_loader = DataLoader(
        val_dataset,
        batch_size=config.batch_size,
        shuffle=False,
        num_workers=0,
        pin_memory=(
            device.type == "cuda"
        ),
    )

    # -------------------------------------------------------------
    # Model
    # -------------------------------------------------------------

    print()
    print("Building longitudinal model...")

    model = build_model(
        config
    )

    model = model.to(device)

    total_parameters, trainable_parameters = (
        count_parameters(model)
    )

    print(
        f"Total parameters: "
        f"{total_parameters:,}"
    )

    print(
        f"Trainable parameters: "
        f"{trainable_parameters:,}"
    )

    # -------------------------------------------------------------
    # Training
    # -------------------------------------------------------------

    print()
    print(
        "Starting training..."
    )

    history = train(
        model=model,
        train_loader=train_loader,
        val_loader=val_loader,
        config=config,
        device=device,
    )

    # -------------------------------------------------------------
    # Final results
    # -------------------------------------------------------------

    print()
    print("=" * 70)
    print("Training completed")
    print("=" * 70)

    if history["val_loss"]:

        best_epoch = int(
            np.argmin(
                history["val_loss"]
            )
        ) + 1

        best_val_loss = history["val_loss"][
            best_epoch - 1
        ]

        best_val_mae = history["val_mae"][
            best_epoch - 1
        ]

        best_val_rmse = history["val_rmse"][
            best_epoch - 1
        ]

        print()
        print(
            f"Best epoch: {best_epoch}"
        )

        print(
            f"Validation loss: "
            f"{best_val_loss:.5f}"
        )

        print(
            f"Validation MAE: "
            f"{best_val_mae:.5f}"
        )

        print(
            f"Validation RMSE: "
            f"{best_val_rmse:.5f}"
        )

    print()
    print(
        f"Best checkpoint: "
        f"{Path(config.output_dir) / config.checkpoint_name}"
    )

    print(
        f"Training history: "
        f"{Path(config.output_dir) / 'training_history.json'}"
    )

    print()


if __name__ == "__main__":
    main()