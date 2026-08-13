"""
training/train_aging.py

Training pipeline for biological skin-aging prediction.

Expected training table:
    data/processed/embeddings/aging_features.csv

Minimum required columns:
    subject_id
    age

All remaining numeric columns are treated as input features.

Example:
    subject_id,age,feat_000,feat_001,feat_002,...
    S001,32,0.12,-0.44,0.81,...
    S002,67,0.31,-0.11,0.27,...

The module:
    1. Loads feature data.
    2. Validates the dataset.
    3. Splits subjects into train/validation/test sets.
    4. Standardizes features using train statistics only.
    5. Trains an MLP regressor.
    6. Uses early stopping.
    7. Reports MAE/RMSE/R².
    8. Saves the best checkpoint.
    9. Saves training history and normalization parameters.

This module is intended as a research/training component.
It does not make clinical decisions.
"""

from __future__ import annotations

import argparse
import json
import random
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
import torch
import torch.nn as nn
from torch.utils.data import DataLoader, Dataset


# ============================================================
# Reproducibility
# ============================================================

def set_seed(seed: int = 42) -> None:
    """
    Set random seeds for reproducible experiments.
    """

    random.seed(seed)
    np.random.seed(seed)

    torch.manual_seed(seed)

    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)

    # Deterministic mode can reduce performance but improves
    # reproducibility.
    torch.backends.cudnn.deterministic = True
    torch.backends.cudnn.benchmark = False


# ============================================================
# Configuration
# ============================================================

@dataclass
class AgingTrainingConfig:
    """
    Configuration for biological-age model training.
    """

    input_csv: str = "data/processed/embeddings/aging_features.csv"

    output_dir: str = "outputs/aging"

    subject_column: str = "subject_id"
    target_column: str = "age"

    hidden_dim: int = 256
    num_hidden_layers: int = 2
    dropout: float = 0.20

    batch_size: int = 32
    learning_rate: float = 1e-3
    weight_decay: float = 1e-4

    epochs: int = 100
    patience: int = 15

    validation_fraction: float = 0.15
    test_fraction: float = 0.15

    seed: int = 42

    num_workers: int = 0

    device: str = "auto"


# ============================================================
# Dataset
# ============================================================

class AgingDataset(Dataset):
    """
    PyTorch dataset for biological-age regression.
    """

    def __init__(
        self,
        features: np.ndarray,
        targets: np.ndarray,
    ) -> None:

        if features.ndim != 2:
            raise ValueError(
                f"Expected 2D feature matrix, got shape {features.shape}"
            )

        if targets.ndim != 1:
            raise ValueError(
                f"Expected 1D target vector, got shape {targets.shape}"
            )

        if len(features) != len(targets):
            raise ValueError(
                "Features and targets must contain the same number of samples."
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
        return len(self.targets)

    def __getitem__(self, index: int):
        return self.features[index], self.targets[index]


# ============================================================
# Model
# ============================================================

class AgingMLP(nn.Module):
    """
    Multi-layer perceptron for biological-age regression.

    Input:
        multimodal skin features / embeddings

    Output:
        predicted biological age
    """

    def __init__(
        self,
        input_dim: int,
        hidden_dim: int = 256,
        num_hidden_layers: int = 2,
        dropout: float = 0.2,
    ) -> None:

        super().__init__()

        if input_dim <= 0:
            raise ValueError("input_dim must be > 0")

        if hidden_dim <= 0:
            raise ValueError("hidden_dim must be > 0")

        if num_hidden_layers < 1:
            raise ValueError("num_hidden_layers must be >= 1")

        layers: List[nn.Module] = []

        current_dim = input_dim

        for _ in range(num_hidden_layers):

            layers.append(
                nn.Linear(
                    current_dim,
                    hidden_dim,
                )
            )

            layers.append(nn.LayerNorm(hidden_dim))
            layers.append(nn.GELU())
            layers.append(nn.Dropout(dropout))

            current_dim = hidden_dim

        layers.append(
            nn.Linear(
                current_dim,
                1,
            )
        )

        self.network = nn.Sequential(*layers)

    def forward(
        self,
        x: torch.Tensor,
    ) -> torch.Tensor:

        return self.network(x).squeeze(-1)


# ============================================================
# Metrics
# ============================================================

def mae(
    predictions: np.ndarray,
    targets: np.ndarray,
) -> float:

    return float(
        np.mean(
            np.abs(predictions - targets)
        )
    )


def rmse(
    predictions: np.ndarray,
    targets: np.ndarray,
) -> float:

    return float(
        np.sqrt(
            np.mean(
                (predictions - targets) ** 2
            )
        )
    )


def r2_score(
    predictions: np.ndarray,
    targets: np.ndarray,
) -> float:

    ss_res = np.sum(
        (targets - predictions) ** 2
    )

    ss_tot = np.sum(
        (targets - np.mean(targets)) ** 2
    )

    if ss_tot == 0:
        return 0.0

    return float(
        1.0 - ss_res / ss_tot
    )


# ============================================================
# Device
# ============================================================

def resolve_device(
    requested: str,
) -> torch.device:

    if requested == "auto":

        if torch.cuda.is_available():
            return torch.device("cuda")

        if getattr(
            torch.backends,
            "mps",
            None,
        ) is not None:

            if torch.backends.mps.is_available():
                return torch.device("mps")

        return torch.device("cpu")

    return torch.device(requested)


# ============================================================
# Data loading
# ============================================================

def load_dataframe(
    path: Path,
    subject_column: str,
    target_column: str,
) -> pd.DataFrame:

    if not path.exists():
        raise FileNotFoundError(
            f"Training file not found: {path}"
        )

    df = pd.read_csv(path)

    if df.empty:
        raise ValueError(
            f"Training file is empty: {path}"
        )

    required_columns = [
        subject_column,
        target_column,
    ]

    missing = [
        column
        for column in required_columns
        if column not in df.columns
    ]

    if missing:
        raise ValueError(
            f"Missing required columns: {missing}"
        )

    df = df.copy()

    df[target_column] = pd.to_numeric(
        df[target_column],
        errors="coerce",
    )

    df = df.dropna(
        subset=[
            subject_column,
            target_column,
        ]
    )

    if len(df) < 10:
        raise ValueError(
            "Dataset contains fewer than 10 valid samples."
        )

    return df


# ============================================================
# Feature preparation
# ============================================================

def select_numeric_features(
    df: pd.DataFrame,
    subject_column: str,
    target_column: str,
) -> Tuple[pd.DataFrame, List[str]]:

    excluded = {
        subject_column,
        target_column,
    }

    candidate_columns = [
        column
        for column in df.columns
        if column not in excluded
    ]

    if not candidate_columns:
        raise ValueError(
            "No feature columns found."
        )

    numeric_columns = []

    for column in candidate_columns:

        converted = pd.to_numeric(
            df[column],
            errors="coerce",
        )

        if converted.notna().sum() > 0:
            numeric_columns.append(column)

    if not numeric_columns:
        raise ValueError(
            "No numeric feature columns found."
        )

    features = df[numeric_columns].copy()

    # Replace infinite values.
    features = features.replace(
        [np.inf, -np.inf],
        np.nan,
    )

    # Median imputation.
    for column in features.columns:

        median = features[column].median()

        if pd.isna(median):
            median = 0.0

        features[column] = features[column].fillna(
            median
        )

    return features, numeric_columns


# ============================================================
# Subject-level splitting
# ============================================================

def split_subjects(
    df: pd.DataFrame,
    subject_column: str,
    validation_fraction: float,
    test_fraction: float,
    seed: int,
) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:

    if validation_fraction < 0:
        raise ValueError(
            "validation_fraction cannot be negative."
        )

    if test_fraction < 0:
        raise ValueError(
            "test_fraction cannot be negative."
        )

    if validation_fraction + test_fraction >= 1:
        raise ValueError(
            "Validation + test fraction must be < 1."
        )

    subjects = (
        df[subject_column]
        .astype(str)
        .unique()
        .tolist()
    )

    if len(subjects) < 3:
        raise ValueError(
            "At least 3 unique subjects are required."
        )

    rng = np.random.default_rng(seed)

    rng.shuffle(subjects)

    n_subjects = len(subjects)

    n_test = max(
        1,
        int(
            round(
                n_subjects * test_fraction
            )
        ),
    )

    n_val = max(
        1,
        int(
            round(
                n_subjects * validation_fraction
            )
        ),
    )

    # Make sure train remains non-empty.
    if n_test + n_val >= n_subjects:
        n_test = 1
        n_val = 1

    test_subjects = set(
        subjects[:n_test]
    )

    val_subjects = set(
        subjects[n_test:n_test + n_val]
    )

    train_subjects = set(
        subjects[n_test + n_val:]
    )

    train_df = df[
        df[subject_column]
        .astype(str)
        .isin(train_subjects)
    ].copy()

    val_df = df[
        df[subject_column]
        .astype(str)
        .isin(val_subjects)
    ].copy()

    test_df = df[
        df[subject_column]
        .astype(str)
        .isin(test_subjects)
    ].copy()

    return (
        train_df,
        val_df,
        test_df,
    )


# ============================================================
# Standardization
# ============================================================

@dataclass
class StandardizationStats:
    mean: Dict[str, float]
    std: Dict[str, float]


def fit_standardization(
    features: pd.DataFrame,
) -> StandardizationStats:

    means = features.mean()

    stds = features.std(
        ddof=0
    )

    # Avoid division by zero for constant features.
    stds = stds.replace(
        0,
        1.0,
    )

    return StandardizationStats(
        mean={
            key: float(value)
            for key, value in means.items()
        },
        std={
            key: float(value)
            for key, value in stds.items()
        },
    )


def apply_standardization(
    features: pd.DataFrame,
    stats: StandardizationStats,
) -> np.ndarray:

    ordered_columns = list(
        stats.mean.keys()
    )

    features = features[
        ordered_columns
    ].copy()

    for column in ordered_columns:

        features[column] = (
            features[column]
            - stats.mean[column]
        ) / stats.std[column]

    return features.to_numpy(
        dtype=np.float32
    )


# ============================================================
# Training / evaluation
# ============================================================

def train_one_epoch(
    model: nn.Module,
    loader: DataLoader,
    optimizer: torch.optim.Optimizer,
    criterion: nn.Module,
    device: torch.device,
) -> float:

    model.train()

    total_loss = 0.0
    total_samples = 0

    for features, targets in loader:

        features = features.to(device)
        targets = targets.to(device)

        optimizer.zero_grad(
            set_to_none=True
        )

        predictions = model(
            features
        )

        loss = criterion(
            predictions,
            targets,
        )

        loss.backward()

        optimizer.step()

        batch_size = features.size(0)

        total_loss += (
            loss.item()
            * batch_size
        )

        total_samples += batch_size

    return total_loss / max(
        total_samples,
        1,
    )


@torch.no_grad()
def evaluate(
    model: nn.Module,
    loader: DataLoader,
    criterion: nn.Module,
    device: torch.device,
) -> Dict[str, float]:

    model.eval()

    total_loss = 0.0
    total_samples = 0

    all_predictions = []
    all_targets = []

    for features, targets in loader:

        features = features.to(device)
        targets = targets.to(device)

        predictions = model(
            features
        )

        loss = criterion(
            predictions,
            targets,
        )

        batch_size = features.size(0)

        total_loss += (
            loss.item()
            * batch_size
        )

        total_samples += batch_size

        all_predictions.append(
            predictions.cpu().numpy()
        )

        all_targets.append(
            targets.cpu().numpy()
        )

    predictions = np.concatenate(
        all_predictions
    )

    targets = np.concatenate(
        all_targets
    )

    return {
        "loss": float(
            total_loss
            / max(total_samples, 1)
        ),
        "mae": mae(
            predictions,
            targets,
        ),
        "rmse": rmse(
            predictions,
            targets,
        ),
        "r2": r2_score(
            predictions,
            targets,
        ),
    }


# ============================================================
# Checkpoint
# ============================================================

def save_checkpoint(
    path: Path,
    model: nn.Module,
    optimizer: torch.optim.Optimizer,
    epoch: int,
    metrics: Dict[str, float],
    config: AgingTrainingConfig,
    feature_names: List[str],
    standardization: StandardizationStats,
) -> None:

    checkpoint = {
        "epoch": epoch,
        "model_state_dict": model.state_dict(),
        "optimizer_state_dict": optimizer.state_dict(),
        "metrics": metrics,
        "config": asdict(config),
        "feature_names": feature_names,
        "standardization": asdict(
            standardization
        ),
    }

    torch.save(
        checkpoint,
        path,
    )


# ============================================================
# Main training function
# ============================================================

def train_aging_model(
    config: AgingTrainingConfig,
) -> Dict[str, object]:

    set_seed(
        config.seed
    )

    output_dir = Path(
        config.output_dir
    )

    output_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    device = resolve_device(
        config.device
    )

    input_path = Path(
        config.input_csv
    )

    print("=" * 60)
    print("BIOLOGICAL AGE TRAINING")
    print("=" * 60)

    print(
        f"Input:  {input_path}"
    )

    print(
        f"Output: {output_dir}"
    )

    print(
        f"Device: {device}"
    )

    # --------------------------------------------------------
    # Load data
    # --------------------------------------------------------

    df = load_dataframe(
        input_path,
        config.subject_column,
        config.target_column,
    )

    print(
        f"Samples: {len(df)}"
    )

    print(
        f"Subjects: "
        f"{df[config.subject_column].nunique()}"
    )

    # --------------------------------------------------------
    # Features
    # --------------------------------------------------------

    feature_df, feature_names = (
        select_numeric_features(
            df,
            config.subject_column,
            config.target_column,
        )
    )

    print(
        f"Features: {len(feature_names)}"
    )

    # --------------------------------------------------------
    # Split by subject
    # --------------------------------------------------------

    train_df, val_df, test_df = (
        split_subjects(
            df,
            config.subject_column,
            config.validation_fraction,
            config.test_fraction,
            config.seed,
        )
    )

    print(
        f"Train samples: {len(train_df)}"
    )

    print(
        f"Validation samples: {len(val_df)}"
    )

    print(
        f"Test samples: {len(test_df)}"
    )

    # --------------------------------------------------------
    # Prepare feature matrices
    # --------------------------------------------------------

    train_features = train_df[
        feature_names
    ].copy()

    val_features = val_df[
        feature_names
    ].copy()

    test_features = test_df[
        feature_names
    ].copy()

    # Numeric conversion.
    train_features = (
        train_features
        .apply(pd.to_numeric, errors="coerce")
    )

    val_features = (
        val_features
        .apply(pd.to_numeric, errors="coerce")
    )

    test_features = (
        test_features
        .apply(pd.to_numeric, errors="coerce")
    )

    # --------------------------------------------------------
    # Imputation using TRAIN statistics only
    # --------------------------------------------------------

    train_medians = train_features.median()

    train_features = train_features.fillna(
        train_medians
    )

    val_features = val_features.fillna(
        train_medians
    )

    test_features = test_features.fillna(
        train_medians
    )

    # --------------------------------------------------------
    # Standardization using TRAIN statistics only
    # --------------------------------------------------------

    standardization = (
        fit_standardization(
            train_features
        )
    )

    X_train = apply_standardization(
        train_features,
        standardization,
    )

    X_val = apply_standardization(
        val_features,
        standardization,
    )

    X_test = apply_standardization(
        test_features,
        standardization,
    )

    y_train = train_df[
        config.target_column
    ].to_numpy(
        dtype=np.float32
    )

    y_val = val_df[
        config.target_column
    ].to_numpy(
        dtype=np.float32
    )

    y_test = test_df[
        config.target_column
    ].to_numpy(
        dtype=np.float32
    )

    # --------------------------------------------------------
    # Datasets
    # --------------------------------------------------------

    train_dataset = AgingDataset(
        X_train,
        y_train,
    )

    val_dataset = AgingDataset(
        X_val,
        y_val,
    )

    test_dataset = AgingDataset(
        X_test,
        y_test,
    )

    train_loader = DataLoader(
        train_dataset,
        batch_size=config.batch_size,
        shuffle=True,
        num_workers=config.num_workers,
    )

    val_loader = DataLoader(
        val_dataset,
        batch_size=config.batch_size,
        shuffle=False,
        num_workers=config.num_workers,
    )

    test_loader = DataLoader(
        test_dataset,
        batch_size=config.batch_size,
        shuffle=False,
        num_workers=config.num_workers,
    )

    # --------------------------------------------------------
    # Model
    # --------------------------------------------------------

    model = AgingMLP(
        input_dim=len(feature_names),
        hidden_dim=config.hidden_dim,
        num_hidden_layers=config.num_hidden_layers,
        dropout=config.dropout,
    ).to(device)

    print(
        f"Model parameters: "
        f"{sum(p.numel() for p in model.parameters())}"
    )

    # --------------------------------------------------------
    # Optimizer
    # --------------------------------------------------------

    criterion = nn.SmoothL1Loss()

    optimizer = torch.optim.AdamW(
        model.parameters(),
        lr=config.learning_rate,
        weight_decay=config.weight_decay,
    )

    # --------------------------------------------------------
    # Training loop
    # --------------------------------------------------------

    best_val_mae = float("inf")

    best_epoch = 0

    patience_counter = 0

    history = []

    checkpoint_path = (
        output_dir
        / "aging_model_best.pt"
    )

    for epoch in range(
        1,
        config.epochs + 1,
    ):

        train_loss = train_one_epoch(
            model,
            train_loader,
            optimizer,
            criterion,
            device,
        )

        val_metrics = evaluate(
            model,
            val_loader,
            criterion,
            device,
        )

        record = {
            "epoch": epoch,
            "train_loss": train_loss,
            **{
                f"val_{key}": value
                for key, value
                in val_metrics.items()
            },
        }

        history.append(
            record
        )

        print(
            f"Epoch {epoch:03d} | "
            f"train_loss={train_loss:.4f} | "
            f"val_loss={val_metrics['loss']:.4f} | "
            f"val_MAE={val_metrics['mae']:.3f} | "
            f"val_RMSE={val_metrics['rmse']:.3f} | "
            f"val_R2={val_metrics['r2']:.3f}"
        )

        # ----------------------------------------------------
        # Early stopping
        # ----------------------------------------------------

        if val_metrics["mae"] < best_val_mae:

            best_val_mae = val_metrics["mae"]

            best_epoch = epoch

            patience_counter = 0

            save_checkpoint(
                checkpoint_path,
                model,
                optimizer,
                epoch,
                val_metrics,
                config,
                feature_names,
                standardization,
            )

        else:

            patience_counter += 1

        if patience_counter >= config.patience:

            print(
                f"Early stopping at epoch "
                f"{epoch}."
            )

            break

    # --------------------------------------------------------
    # Save training history
    # --------------------------------------------------------

    history_path = (
        output_dir
        / "training_history.csv"
    )

    pd.DataFrame(
        history
    ).to_csv(
        history_path,
        index=False,
    )

    # --------------------------------------------------------
    # Load best checkpoint
    # --------------------------------------------------------

    checkpoint = torch.load(
        checkpoint_path,
        map_location=device,
        weights_only=False,
    )

    model.load_state_dict(
        checkpoint[
            "model_state_dict"
        ]
    )

    # --------------------------------------------------------
    # Final evaluation
    # --------------------------------------------------------

    test_metrics = evaluate(
        model,
        test_loader,
        criterion,
        device,
    )

    print()
    print("=" * 60)
    print("FINAL TEST RESULTS")
    print("=" * 60)

    print(
        f"MAE:  {test_metrics['mae']:.3f} years"
    )

    print(
        f"RMSE: {test_metrics['rmse']:.3f} years"
    )

    print(
        f"R²:   {test_metrics['r2']:.3f}"
    )

    print(
        f"Best epoch: {best_epoch}"
    )

    # --------------------------------------------------------
    # Save metadata
    # --------------------------------------------------------

    metadata = {
        "task": "biological_age_regression",
        "input_csv": str(input_path),
        "num_samples": int(len(df)),
        "num_subjects": int(
            df[
                config.subject_column
            ].nunique()
        ),
        "num_features": len(
            feature_names
        ),
        "feature_names": feature_names,
        "best_epoch": best_epoch,
        "best_validation_mae": best_val_mae,
        "test_metrics": test_metrics,
        "device": str(device),
        "config": asdict(config),
    }

    metadata_path = (
        output_dir
        / "training_metadata.json"
    )

    with open(
        metadata_path,
        "w",
        encoding="utf-8",
    ) as file:

        json.dump(
            metadata,
            file,
            indent=2,
        )

    print()
    print(
        f"Checkpoint: {checkpoint_path}"
    )

    print(
        f"History:    {history_path}"
    )

    print(
        f"Metadata:   {metadata_path}"
    )

    print()
    print(
        "Aging model training complete."
    )

    return {
        "model": model,
        "checkpoint": checkpoint_path,
        "history": history,
        "test_metrics": test_metrics,
        "feature_names": feature_names,
        "standardization": standardization,
    }


# ============================================================
# CLI
# ============================================================

def build_parser() -> argparse.ArgumentParser:

    parser = argparse.ArgumentParser(
        description=(
            "Train biological-age regression model."
        )
    )

    parser.add_argument(
        "--input",
        default=(
            "data/processed/embeddings/"
            "aging_features.csv"
        ),
        help="Input CSV containing features and age.",
    )

    parser.add_argument(
        "--output",
        default="outputs/aging",
        help="Output directory.",
    )

    parser.add_argument(
        "--epochs",
        type=int,
        default=100,
    )

    parser.add_argument(
        "--batch-size",
        type=int,
        default=32,
    )

    parser.add_argument(
        "--learning-rate",
        type=float,
        default=1e-3,
    )

    parser.add_argument(
        "--hidden-dim",
        type=int,
        default=256,
    )

    parser.add_argument(
        "--dropout",
        type=float,
        default=0.2,
    )

    parser.add_argument(
        "--patience",
        type=int,
        default=15,
    )

    parser.add_argument(
        "--seed",
        type=int,
        default=42,
    )

    parser.add_argument(
        "--device",
        default="auto",
        choices=[
            "auto",
            "cpu",
            "cuda",
            "mps",
        ],
    )

    return parser


def main() -> None:

    parser = build_parser()

    args = parser.parse_args()

    config = AgingTrainingConfig(
        input_csv=args.input,
        output_dir=args.output,
        epochs=args.epochs,
        batch_size=args.batch_size,
        learning_rate=args.learning_rate,
        hidden_dim=args.hidden_dim,
        dropout=args.dropout,
        patience=args.patience,
        seed=args.seed,
        device=args.device,
    )

    train_aging_model(
        config
    )


if __name__ == "__main__":
    main()