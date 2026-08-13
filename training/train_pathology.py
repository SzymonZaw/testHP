"""
train_pathology.py

Training pipeline for the pathology classification model.

Expected input:
    - precomputed embeddings/features
    - labels describing pathology classes

Example classes:
    0 -> normal
    1 -> bcc
    2 -> melanoma

The script supports:
    - loading features from .pt, .npy, .npz or .csv
    - train/validation split
    - class-weighted loss
    - model training
    - validation
    - accuracy, precision, recall, F1
    - confusion matrix
    - checkpoint saving
    - training history
    - reproducibility
"""

from __future__ import annotations

import argparse
import json
import random
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np
import torch
import torch.nn as nn
from torch.utils.data import DataLoader, TensorDataset

try:
    from sklearn.metrics import (
        accuracy_score,
        classification_report,
        confusion_matrix,
        precision_recall_fscore_support,
    )
    from sklearn.model_selection import train_test_split

    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False


# ---------------------------------------------------------------------
# Project imports
# ---------------------------------------------------------------------

try:
    from models.pathology_model import PathologyModel
except ImportError:
    PathologyModel = None


# ---------------------------------------------------------------------
# Reproducibility
# ---------------------------------------------------------------------

def set_seed(seed: int = 42) -> None:
    """
    Set random seeds for reproducible training.
    """

    random.seed(seed)
    np.random.seed(seed)

    torch.manual_seed(seed)

    if torch.cuda.is_available():
        torch.cuda.manual_seed(seed)
        torch.cuda.manual_seed_all(seed)

    # Deterministic mode improves reproducibility.
    # It can reduce performance on some CUDA operations.
    torch.backends.cudnn.deterministic = True
    torch.backends.cudnn.benchmark = False


# ---------------------------------------------------------------------
# Device
# ---------------------------------------------------------------------

def get_device() -> torch.device:
    """
    Select CUDA when available, otherwise CPU.
    """

    return torch.device(
        "cuda" if torch.cuda.is_available() else "cpu"
    )


# ---------------------------------------------------------------------
# Data loading
# ---------------------------------------------------------------------

def load_features(
    feature_path: str | Path,
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Load features and labels.

    Supported formats:

        .pt
        .pth
        .npy
        .npz
        .csv

    Expected structures:

    PyTorch:
        {
            "features": Tensor[N, D],
            "labels": Tensor[N]
        }

    NumPy:
        features.npy
        labels.npy

    NPZ:
        features=...
        labels=...

    CSV:
        last column should contain label,
        remaining columns are features.
    """

    path = Path(feature_path)

    if not path.exists():
        raise FileNotFoundError(
            f"Feature file does not exist: {path}"
        )

    suffix = path.suffix.lower()

    # --------------------------------------------------------------
    # PyTorch
    # --------------------------------------------------------------

    if suffix in {".pt", ".pth"}:

        data = torch.load(
            path,
            map_location="cpu",
        )

        if isinstance(data, dict):

            if "features" not in data:
                raise KeyError(
                    "PyTorch file must contain key 'features'."
                )

            if "labels" not in data:
                raise KeyError(
                    "PyTorch file must contain key 'labels'."
                )

            features = data["features"]
            labels = data["labels"]

        elif isinstance(data, (tuple, list)) and len(data) == 2:

            features, labels = data

        else:
            raise ValueError(
                "Unsupported PyTorch feature structure."
            )

        if torch.is_tensor(features):
            features = features.detach().cpu().numpy()

        if torch.is_tensor(labels):
            labels = labels.detach().cpu().numpy()

        return (
            np.asarray(features, dtype=np.float32),
            np.asarray(labels),
        )

    # --------------------------------------------------------------
    # NumPy
    # --------------------------------------------------------------

    if suffix == ".npy":

        features = np.load(path)

        label_path = path.with_name(
            f"{path.stem}_labels.npy"
        )

        if not label_path.exists():
            raise FileNotFoundError(
                f"Could not find corresponding labels file: "
                f"{label_path}"
            )

        labels = np.load(label_path)

        return (
            np.asarray(features, dtype=np.float32),
            np.asarray(labels),
        )

    # --------------------------------------------------------------
    # NPZ
    # --------------------------------------------------------------

    if suffix == ".npz":

        data = np.load(path)

        if "features" not in data:
            raise KeyError(
                "NPZ file must contain 'features'."
            )

        if "labels" not in data:
            raise KeyError(
                "NPZ file must contain 'labels'."
            )

        return (
            np.asarray(
                data["features"],
                dtype=np.float32,
            ),
            np.asarray(data["labels"]),
        )

    # --------------------------------------------------------------
    # CSV
    # --------------------------------------------------------------

    if suffix == ".csv":

        data = np.genfromtxt(
            path,
            delimiter=",",
            names=True,
        )

        if data.dtype.names is None:
            raise ValueError(
                "CSV must contain a header."
            )

        columns = list(data.dtype.names)

        if "label" in columns:
            label_column = "label"
        else:
            label_column = columns[-1]

        feature_columns = [
            c for c in columns
            if c != label_column
        ]

        features = np.column_stack(
            [data[c] for c in feature_columns]
        )

        labels = data[label_column]

        return (
            np.asarray(features, dtype=np.float32),
            np.asarray(labels),
        )

    raise ValueError(
        f"Unsupported feature format: {suffix}"
    )


# ---------------------------------------------------------------------
# Label encoding
# ---------------------------------------------------------------------

def encode_labels(
    labels: np.ndarray,
) -> Tuple[np.ndarray, Dict[str, int]]:
    """
    Convert labels into integer class IDs.

    Example:

        normal   -> 0
        bcc      -> 1
        melanoma -> 2
    """

    labels = np.asarray(labels)

    # Already integer labels.
    if np.issubdtype(labels.dtype, np.integer):

        unique = sorted(
            np.unique(labels).tolist()
        )

        mapping = {
            str(value): int(value)
            for value in unique
        }

        return labels.astype(np.int64), mapping

    # String labels.
    labels = labels.astype(str)

    unique_labels = sorted(
        np.unique(labels).tolist()
    )

    mapping = {
        label: index
        for index, label in enumerate(unique_labels)
    }

    encoded = np.array(
        [mapping[label] for label in labels],
        dtype=np.int64,
    )

    return encoded, mapping


# ---------------------------------------------------------------------
# Dataset split
# ---------------------------------------------------------------------

def split_dataset(
    features: np.ndarray,
    labels: np.ndarray,
    validation_fraction: float = 0.2,
    seed: int = 42,
) -> Tuple[
    np.ndarray,
    np.ndarray,
    np.ndarray,
    np.ndarray,
]:
    """
    Stratified train/validation split.
    """

    if not 0.0 < validation_fraction < 1.0:
        raise ValueError(
            "validation_fraction must be between 0 and 1."
        )

    if SKLEARN_AVAILABLE:

        x_train, x_val, y_train, y_val = train_test_split(
            features,
            labels,
            test_size=validation_fraction,
            random_state=seed,
            stratify=labels,
        )

        return (
            x_train,
            x_val,
            y_train,
            y_val,
        )

    # --------------------------------------------------------------
    # Fallback without sklearn
    # --------------------------------------------------------------

    rng = np.random.default_rng(seed)

    train_indices: List[int] = []
    val_indices: List[int] = []

    for class_id in np.unique(labels):

        indices = np.where(
            labels == class_id
        )[0]

        rng.shuffle(indices)

        n_val = max(
            1,
            int(len(indices) * validation_fraction),
        )

        val_indices.extend(
            indices[:n_val].tolist()
        )

        train_indices.extend(
            indices[n_val:].tolist()
        )

    train_indices = np.asarray(train_indices)
    val_indices = np.asarray(val_indices)

    rng.shuffle(train_indices)
    rng.shuffle(val_indices)

    return (
        features[train_indices],
        features[val_indices],
        labels[train_indices],
        labels[val_indices],
    )


# ---------------------------------------------------------------------
# Class weights
# ---------------------------------------------------------------------

def calculate_class_weights(
    labels: np.ndarray,
    num_classes: int,
) -> torch.Tensor:
    """
    Calculate inverse-frequency class weights.

    This is useful because pathology datasets are often highly
    imbalanced.
    """

    counts = np.bincount(
        labels,
        minlength=num_classes,
    ).astype(np.float32)

    counts[counts == 0] = 1.0

    weights = (
        len(labels)
        / (num_classes * counts)
    )

    weights = weights / weights.mean()

    return torch.tensor(
        weights,
        dtype=torch.float32,
    )


# ---------------------------------------------------------------------
# Model creation
# ---------------------------------------------------------------------

def create_model(
    input_dim: int,
    num_classes: int,
    hidden_dim: int = 512,
    dropout: float = 0.2,
) -> nn.Module:
    """
    Create pathology model.

    Uses models/pathology_model.py when available.
    """

    if PathologyModel is None:

        raise ImportError(
            "Could not import PathologyModel from "
            "models.pathology_model"
        )

    # Try the most explicit constructor first.
    try:

        model = PathologyModel(
            input_dim=input_dim,
            hidden_dim=hidden_dim,
            num_classes=num_classes,
            dropout=dropout,
        )

        return model

    except TypeError:
        pass

    # Fallback for a simpler constructor.
    try:

        model = PathologyModel(
            input_dim=input_dim,
            num_classes=num_classes,
        )

        return model

    except TypeError as exc:

        raise TypeError(
            "PathologyModel constructor does not match "
            "the expected interface."
        ) from exc


# ---------------------------------------------------------------------
# Training
# ---------------------------------------------------------------------

def train_one_epoch(
    model: nn.Module,
    loader: DataLoader,
    optimizer: torch.optim.Optimizer,
    criterion: nn.Module,
    device: torch.device,
) -> Tuple[float, float]:

    model.train()

    running_loss = 0.0
    correct = 0
    total = 0

    for features, labels in loader:

        features = features.to(device)
        labels = labels.to(device)

        optimizer.zero_grad(
            set_to_none=True
        )

        outputs = model(features)

        # Support models returning dictionaries.
        if isinstance(outputs, dict):

            if "logits" in outputs:
                logits = outputs["logits"]

            elif "output" in outputs:
                logits = outputs["output"]

            else:
                raise KeyError(
                    "Model dictionary output must contain "
                    "'logits' or 'output'."
                )

        else:
            logits = outputs

        loss = criterion(
            logits,
            labels,
        )

        loss.backward()

        optimizer.step()

        running_loss += (
            loss.item()
            * labels.size(0)
        )

        predictions = torch.argmax(
            logits,
            dim=1,
        )

        correct += (
            predictions == labels
        ).sum().item()

        total += labels.size(0)

    epoch_loss = (
        running_loss / total
        if total > 0
        else 0.0
    )

    epoch_accuracy = (
        correct / total
        if total > 0
        else 0.0
    )

    return (
        epoch_loss,
        epoch_accuracy,
    )


# ---------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------

@torch.no_grad()
def validate(
    model: nn.Module,
    loader: DataLoader,
    criterion: nn.Module,
    device: torch.device,
) -> Dict:

    model.eval()

    running_loss = 0.0
    total = 0

    all_labels = []
    all_predictions = []
    all_probabilities = []

    for features, labels in loader:

        features = features.to(device)
        labels = labels.to(device)

        outputs = model(features)

        if isinstance(outputs, dict):

            if "logits" in outputs:
                logits = outputs["logits"]

            elif "output" in outputs:
                logits = outputs["output"]

            else:
                raise KeyError(
                    "Model dictionary output must contain "
                    "'logits' or 'output'."
                )

        else:
            logits = outputs

        loss = criterion(
            logits,
            labels,
        )

        probabilities = torch.softmax(
            logits,
            dim=1,
        )

        predictions = torch.argmax(
            probabilities,
            dim=1,
        )

        running_loss += (
            loss.item()
            * labels.size(0)
        )

        total += labels.size(0)

        all_labels.extend(
            labels.cpu().numpy().tolist()
        )

        all_predictions.extend(
            predictions.cpu().numpy().tolist()
        )

        all_probabilities.extend(
            probabilities.cpu().numpy().tolist()
        )

    if total == 0:
        return {
            "loss": 0.0,
            "accuracy": 0.0,
            "labels": [],
            "predictions": [],
            "probabilities": [],
        }

    labels_np = np.asarray(
        all_labels
    )

    predictions_np = np.asarray(
        all_predictions
    )

    probabilities_np = np.asarray(
        all_probabilities
    )

    loss = running_loss / total

    if SKLEARN_AVAILABLE:

        accuracy = accuracy_score(
            labels_np,
            predictions_np,
        )

        precision, recall, f1, _ = (
            precision_recall_fscore_support(
                labels_np,
                predictions_np,
                average="weighted",
                zero_division=0,
            )
        )

        cm = confusion_matrix(
            labels_np,
            predictions_np,
        ).tolist()

    else:

        accuracy = float(
            np.mean(
                labels_np == predictions_np
            )
        )

        precision = 0.0
        recall = 0.0
        f1 = 0.0

        cm = []

    return {
        "loss": float(loss),
        "accuracy": float(accuracy),
        "precision": float(precision),
        "recall": float(recall),
        "f1": float(f1),
        "confusion_matrix": cm,
        "labels": labels_np.tolist(),
        "predictions": predictions_np.tolist(),
        "probabilities": probabilities_np.tolist(),
    }


# ---------------------------------------------------------------------
# Checkpoint
# ---------------------------------------------------------------------

def save_checkpoint(
    path: Path,
    model: nn.Module,
    optimizer: torch.optim.Optimizer,
    epoch: int,
    metrics: Dict,
    label_mapping: Dict[str, int],
    config: Dict,
) -> None:
    """
    Save complete training checkpoint.
    """

    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    checkpoint = {
        "epoch": epoch,
        "model_state_dict": model.state_dict(),
        "optimizer_state_dict": optimizer.state_dict(),
        "metrics": metrics,
        "label_mapping": label_mapping,
        "config": config,
    }

    torch.save(
        checkpoint,
        path,
    )


# ---------------------------------------------------------------------
# Training history
# ---------------------------------------------------------------------

def save_history(
    path: Path,
    history: Dict,
) -> None:

    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with open(
        path,
        "w",
        encoding="utf-8",
    ) as file:

        json.dump(
            history,
            file,
            indent=2,
        )


# ---------------------------------------------------------------------
# Main training function
# ---------------------------------------------------------------------

def train_pathology(
    feature_path: str | Path,
    output_dir: str | Path,
    epochs: int = 30,
    batch_size: int = 32,
    learning_rate: float = 1e-4,
    weight_decay: float = 1e-5,
    validation_fraction: float = 0.2,
    hidden_dim: int = 512,
    dropout: float = 0.2,
    seed: int = 42,
) -> Dict:

    set_seed(seed)

    device = get_device()

    output_dir = Path(output_dir)

    output_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    # --------------------------------------------------------------
    # Load data
    # --------------------------------------------------------------

    features, labels = load_features(
        feature_path
    )

    if features.ndim != 2:
        raise ValueError(
            f"Expected features with shape [N, D], "
            f"got {features.shape}"
        )

    if len(features) != len(labels):
        raise ValueError(
            "Number of features and labels must match."
        )

    labels, label_mapping = encode_labels(
        labels
    )

    num_classes = len(
        np.unique(labels)
    )

    input_dim = features.shape[1]

    print("=" * 70)
    print("Pathology Model Training")
    print("=" * 70)

    print(f"Features:      {features.shape}")
    print(f"Input dim:     {input_dim}")
    print(f"Samples:       {len(features)}")
    print(f"Classes:       {num_classes}")
    print(f"Label mapping: {label_mapping}")
    print(f"Device:        {device}")

    # --------------------------------------------------------------
    # Split
    # --------------------------------------------------------------

    (
        x_train,
        x_val,
        y_train,
        y_val,
    ) = split_dataset(
        features,
        labels,
        validation_fraction=validation_fraction,
        seed=seed,
    )

    print(
        f"Training samples:   {len(x_train)}"
    )

    print(
        f"Validation samples: {len(x_val)}"
    )

    # --------------------------------------------------------------
    # Tensor datasets
    # --------------------------------------------------------------

    train_dataset = TensorDataset(
        torch.tensor(
            x_train,
            dtype=torch.float32,
        ),
        torch.tensor(
            y_train,
            dtype=torch.long,
        ),
    )

    val_dataset = TensorDataset(
        torch.tensor(
            x_val,
            dtype=torch.float32,
        ),
        torch.tensor(
            y_val,
            dtype=torch.long,
        ),
    )

    train_loader = DataLoader(
        train_dataset,
        batch_size=batch_size,
        shuffle=True,
        num_workers=0,
        pin_memory=torch.cuda.is_available(),
    )

    val_loader = DataLoader(
        val_dataset,
        batch_size=batch_size,
        shuffle=False,
        num_workers=0,
        pin_memory=torch.cuda.is_available(),
    )

    # --------------------------------------------------------------
    # Model
    # --------------------------------------------------------------

    model = create_model(
        input_dim=input_dim,
        num_classes=num_classes,
        hidden_dim=hidden_dim,
        dropout=dropout,
    )

    model = model.to(device)

    # --------------------------------------------------------------
    # Class-weighted loss
    # --------------------------------------------------------------

    class_weights = calculate_class_weights(
        y_train,
        num_classes,
    ).to(device)

    criterion = nn.CrossEntropyLoss(
        weight=class_weights
    )

    # --------------------------------------------------------------
    # Optimizer
    # --------------------------------------------------------------

    optimizer = torch.optim.AdamW(
        model.parameters(),
        lr=learning_rate,
        weight_decay=weight_decay,
    )

    scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(
        optimizer,
        mode="max",
        factor=0.5,
        patience=3,
    )

    # --------------------------------------------------------------
    # Training
    # --------------------------------------------------------------

    history = {
        "train_loss": [],
        "train_accuracy": [],
        "val_loss": [],
        "val_accuracy": [],
        "val_precision": [],
        "val_recall": [],
        "val_f1": [],
    }

    best_f1 = -float("inf")
    best_epoch = -1

    best_checkpoint = (
        output_dir / "pathology_best.pt"
    )

    last_checkpoint = (
        output_dir / "pathology_last.pt"
    )

    for epoch in range(1, epochs + 1):

        train_loss, train_accuracy = (
            train_one_epoch(
                model=model,
                loader=train_loader,
                optimizer=optimizer,
                criterion=criterion,
                device=device,
            )
        )

        validation = validate(
            model=model,
            loader=val_loader,
            criterion=criterion,
            device=device,
        )

        scheduler.step(
            validation["f1"]
        )

        history["train_loss"].append(
            train_loss
        )

        history["train_accuracy"].append(
            train_accuracy
        )

        history["val_loss"].append(
            validation["loss"]
        )

        history["val_accuracy"].append(
            validation["accuracy"]
        )

        history["val_precision"].append(
            validation["precision"]
        )

        history["val_recall"].append(
            validation["recall"]
        )

        history["val_f1"].append(
            validation["f1"]
        )

        print(
            f"Epoch {epoch:03d}/{epochs:03d} | "
            f"train_loss={train_loss:.4f} | "
            f"train_acc={train_accuracy:.4f} | "
            f"val_loss={validation['loss']:.4f} | "
            f"val_acc={validation['accuracy']:.4f} | "
            f"val_f1={validation['f1']:.4f}"
        )

        # ----------------------------------------------------------
        # Best checkpoint
        # ----------------------------------------------------------

        if validation["f1"] > best_f1:

            best_f1 = validation["f1"]
            best_epoch = epoch

            save_checkpoint(
                path=best_checkpoint,
                model=model,
                optimizer=optimizer,
                epoch=epoch,
                metrics=validation,
                label_mapping=label_mapping,
                config={
                    "input_dim": input_dim,
                    "hidden_dim": hidden_dim,
                    "num_classes": num_classes,
                    "dropout": dropout,
                    "learning_rate": learning_rate,
                    "weight_decay": weight_decay,
                    "batch_size": batch_size,
                    "epochs": epochs,
                    "seed": seed,
                },
            )

    # --------------------------------------------------------------
    # Last checkpoint
    # --------------------------------------------------------------

    save_checkpoint(
        path=last_checkpoint,
        model=model,
        optimizer=optimizer,
        epoch=epochs,
        metrics=validation,
        label_mapping=label_mapping,
        config={
            "input_dim": input_dim,
            "hidden_dim": hidden_dim,
            "num_classes": num_classes,
            "dropout": dropout,
            "learning_rate": learning_rate,
            "weight_decay": weight_decay,
            "batch_size": batch_size,
            "epochs": epochs,
            "seed": seed,
        },
    )

    # --------------------------------------------------------------
    # Save history
    # --------------------------------------------------------------

    save_history(
        output_dir / "training_history.json",
        history,
    )

    # --------------------------------------------------------------
    # Classification report
    # --------------------------------------------------------------

    if SKLEARN_AVAILABLE:

        report = classification_report(
            validation["labels"],
            validation["predictions"],
            zero_division=0,
        )

        print()
        print("Classification report:")
        print(report)

        with open(
            output_dir / "classification_report.txt",
            "w",
            encoding="utf-8",
        ) as file:

            file.write(report)

    # --------------------------------------------------------------
    # Final information
    # --------------------------------------------------------------

    summary = {
        "input_dim": input_dim,
        "num_classes": num_classes,
        "num_samples": len(features),
        "train_samples": len(x_train),
        "validation_samples": len(x_val),
        "best_epoch": best_epoch,
        "best_f1": best_f1,
        "label_mapping": label_mapping,
        "device": str(device),
        "best_checkpoint": str(
            best_checkpoint
        ),
        "last_checkpoint": str(
            last_checkpoint
        ),
    }

    with open(
        output_dir / "training_summary.json",
        "w",
        encoding="utf-8",
    ) as file:

        json.dump(
            summary,
            file,
            indent=2,
        )

    print()
    print("=" * 70)
    print("Training finished.")
    print("=" * 70)

    print(
        f"Best epoch: {best_epoch}"
    )

    print(
        f"Best validation F1: {best_f1:.4f}"
    )

    print(
        f"Checkpoint: {best_checkpoint}"
    )

    return summary


# ---------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:

    parser = argparse.ArgumentParser(
        description=(
            "Train the pathology classification model."
        )
    )

    parser.add_argument(
        "--features",
        type=str,
        required=True,
        help=(
            "Path to feature file "
            "(.pt/.pth/.npy/.npz/.csv)."
        ),
    )

    parser.add_argument(
        "--output",
        type=str,
        default="outputs/pathology",
        help=(
            "Output directory for checkpoints "
            "and training results."
        ),
    )

    parser.add_argument(
        "--epochs",
        type=int,
        default=30,
    )

    parser.add_argument(
        "--batch-size",
        type=int,
        default=32,
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
        "--validation-fraction",
        type=float,
        default=0.2,
    )

    parser.add_argument(
        "--hidden-dim",
        type=int,
        default=512,
    )

    parser.add_argument(
        "--dropout",
        type=float,
        default=0.2,
    )

    parser.add_argument(
        "--seed",
        type=int,
        default=42,
    )

    return parser


# ---------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------

def main() -> None:

    parser = build_parser()

    args = parser.parse_args()

    train_pathology(
        feature_path=args.features,
        output_dir=args.output,
        epochs=args.epochs,
        batch_size=args.batch_size,
        learning_rate=args.learning_rate,
        weight_decay=args.weight_decay,
        validation_fraction=args.validation_fraction,
        hidden_dim=args.hidden_dim,
        dropout=args.dropout,
        seed=args.seed,
    )


if __name__ == "__main__":
    main()