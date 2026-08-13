# training/train_abnormality.py

"""
Abnormality Model Training
==========================

Trains the abnormality classifier using precomputed feature embeddings.

Expected dataset structure:

data/
└── processed/
    └── embeddings/
        └── abnormality/
            ├── normal/
            │   ├── sample_001.npy
            │   ├── sample_002.npy
            │   └── ...
            │
            └── abnormal/
                ├── sample_101.npy
                ├── sample_102.npy
                └── ...

Each .npy file should contain one embedding vector:

    shape = (768,)

or:

    shape = (1, 768)

The default input dimension is 768, matching the embedding
dimension used by the abnormality model.

Outputs:

outputs/
└── abnormalities/
    ├── best_model.pt
    ├── last_model.pt
    ├── training_history.json
    └── metrics.json
"""

from __future__ import annotations

import argparse
import json
import random
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Tuple

import numpy as np
import torch
from torch import nn
from torch.utils.data import DataLoader, Dataset, random_split


# ---------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[1]

DEFAULT_DATA_DIR = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "embeddings"
    / "abnormality"
)

DEFAULT_OUTPUT_DIR = (
    PROJECT_ROOT
    / "outputs"
    / "abnormalities"
)


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

    # Reproducibility is preferred for experiments.
    torch.backends.cudnn.deterministic = True
    torch.backends.cudnn.benchmark = False


# ---------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------

@dataclass
class TrainingConfig:
    input_dim: int = 768
    hidden_dim: int = 512
    num_classes: int = 2

    dropout: float = 0.2

    learning_rate: float = 1e-4
    weight_decay: float = 1e-5

    batch_size: int = 32
    epochs: int = 30

    validation_split: float = 0.2

    seed: int = 42

    num_workers: int = 0

    early_stopping_patience: int = 7


# ---------------------------------------------------------------------
# Dataset
# ---------------------------------------------------------------------

class AbnormalityEmbeddingDataset(Dataset):
    """
    Dataset loading precomputed embeddings from .npy files.

    Classes:

        normal   -> 0
        abnormal -> 1
    """

    CLASS_NAMES = {
        "normal": 0,
        "abnormal": 1,
    }

    def __init__(
        self,
        root_dir: str | Path,
        input_dim: int = 768,
    ):
        self.root_dir = Path(root_dir)
        self.input_dim = input_dim

        self.samples: List[Tuple[Path, int]] = []

        self._collect_samples()

        if not self.samples:
            raise RuntimeError(
                f"No .npy embeddings found in: {self.root_dir}\n\n"
                "Expected structure:\n"
                "abnormality/normal/*.npy\n"
                "abnormality/abnormal/*.npy"
            )

    def _collect_samples(self) -> None:
        for class_name, label in self.CLASS_NAMES.items():

            class_dir = self.root_dir / class_name

            if not class_dir.exists():
                continue

            files = sorted(class_dir.rglob("*.npy"))

            for file_path in files:
                self.samples.append(
                    (file_path, label)
                )

    def __len__(self) -> int:
        return len(self.samples)

    def __getitem__(
        self,
        index: int,
    ) -> Tuple[torch.Tensor, torch.Tensor]:

        file_path, label = self.samples[index]

        embedding = np.load(file_path)

        embedding = np.asarray(
            embedding,
            dtype=np.float32,
        )

        # Accept:
        #
        # (768,)
        #
        # or:
        #
        # (1, 768)
        #
        # or other singleton dimensions.

        embedding = np.squeeze(embedding)

        if embedding.ndim != 1:
            raise ValueError(
                f"Invalid embedding shape {embedding.shape} "
                f"for file: {file_path}"
            )

        if embedding.shape[0] != self.input_dim:
            raise ValueError(
                f"Embedding dimension mismatch in {file_path}. "
                f"Expected {self.input_dim}, "
                f"got {embedding.shape[0]}."
            )

        x = torch.from_numpy(embedding)

        y = torch.tensor(
            label,
            dtype=torch.long,
        )

        return x, y


# ---------------------------------------------------------------------
# Model
# ---------------------------------------------------------------------

class AbnormalityClassifier(nn.Module):
    """
    Neural network for binary abnormality classification.

    Architecture:

        embedding
            ↓
        Linear
            ↓
        ReLU
            ↓
        Dropout
            ↓
        Linear
            ↓
        logits
    """

    def __init__(
        self,
        input_dim: int = 768,
        hidden_dim: int = 512,
        num_classes: int = 2,
        dropout: float = 0.2,
    ):
        super().__init__()

        self.input_dim = input_dim
        self.hidden_dim = hidden_dim
        self.num_classes = num_classes

        self.network = nn.Sequential(
            nn.Linear(
                input_dim,
                hidden_dim,
            ),

            nn.ReLU(),

            nn.Dropout(
                dropout,
            ),

            nn.Linear(
                hidden_dim,
                num_classes,
            ),
        )

    def forward(
        self,
        x: torch.Tensor,
    ) -> torch.Tensor:

        return self.network(x)


# ---------------------------------------------------------------------
# Metrics
# ---------------------------------------------------------------------

def calculate_metrics(
    logits: torch.Tensor,
    targets: torch.Tensor,
) -> Dict[str, float]:

    predictions = torch.argmax(
        logits,
        dim=1,
    )

    correct = (
        predictions == targets
    ).sum().item()

    total = targets.numel()

    accuracy = (
        correct / total
        if total > 0
        else 0.0
    )

    # Binary metrics
    tp = (
        (predictions == 1)
        & (targets == 1)
    ).sum().item()

    tn = (
        (predictions == 0)
        & (targets == 0)
    ).sum().item()

    fp = (
        (predictions == 1)
        & (targets == 0)
    ).sum().item()

    fn = (
        (predictions == 0)
        & (targets == 1)
    ).sum().item()

    precision = (
        tp / (tp + fp)
        if (tp + fp) > 0
        else 0.0
    )

    recall = (
        tp / (tp + fn)
        if (tp + fn) > 0
        else 0.0
    )

    f1 = (
        2 * precision * recall
        / (precision + recall)
        if (precision + recall) > 0
        else 0.0
    )

    return {
        "accuracy": float(accuracy),
        "precision": float(precision),
        "recall": float(recall),
        "f1": float(f1),
        "true_positive": float(tp),
        "true_negative": float(tn),
        "false_positive": float(fp),
        "false_negative": float(fn),
    }


# ---------------------------------------------------------------------
# Training
# ---------------------------------------------------------------------

def train_one_epoch(
    model: nn.Module,
    loader: DataLoader,
    criterion: nn.Module,
    optimizer: torch.optim.Optimizer,
    device: torch.device,
) -> Tuple[float, Dict[str, float]]:

    model.train()

    total_loss = 0.0

    all_logits = []
    all_targets = []

    for embeddings, targets in loader:

        embeddings = embeddings.to(
            device,
            non_blocking=True,
        )

        targets = targets.to(
            device,
            non_blocking=True,
        )

        optimizer.zero_grad()

        logits = model(
            embeddings
        )

        loss = criterion(
            logits,
            targets,
        )

        loss.backward()

        optimizer.step()

        total_loss += (
            loss.item()
            * embeddings.size(0)
        )

        all_logits.append(
            logits.detach().cpu()
        )

        all_targets.append(
            targets.detach().cpu()
        )

    epoch_loss = (
        total_loss / len(loader.dataset)
    )

    logits = torch.cat(
        all_logits,
        dim=0,
    )

    targets = torch.cat(
        all_targets,
        dim=0,
    )

    metrics = calculate_metrics(
        logits,
        targets,
    )

    return epoch_loss, metrics


# ---------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------

@torch.no_grad()
def validate(
    model: nn.Module,
    loader: DataLoader,
    criterion: nn.Module,
    device: torch.device,
) -> Tuple[float, Dict[str, float]]:

    model.eval()

    total_loss = 0.0

    all_logits = []
    all_targets = []

    for embeddings, targets in loader:

        embeddings = embeddings.to(
            device,
            non_blocking=True,
        )

        targets = targets.to(
            device,
            non_blocking=True,
        )

        logits = model(
            embeddings
        )

        loss = criterion(
            logits,
            targets,
        )

        total_loss += (
            loss.item()
            * embeddings.size(0)
        )

        all_logits.append(
            logits.cpu()
        )

        all_targets.append(
            targets.cpu()
        )

    validation_loss = (
        total_loss / len(loader.dataset)
    )

    logits = torch.cat(
        all_logits,
        dim=0,
    )

    targets = torch.cat(
        all_targets,
        dim=0,
    )

    metrics = calculate_metrics(
        logits,
        targets,
    )

    return validation_loss, metrics


# ---------------------------------------------------------------------
# Save helpers
# ---------------------------------------------------------------------

def save_checkpoint(
    model: nn.Module,
    optimizer: torch.optim.Optimizer,
    epoch: int,
    metrics: Dict[str, float],
    config: TrainingConfig,
    path: Path,
) -> None:

    checkpoint = {
        "epoch": epoch,

        "model_state_dict":
            model.state_dict(),

        "optimizer_state_dict":
            optimizer.state_dict(),

        "metrics":
            metrics,

        "config":
            vars(config),
    }

    torch.save(
        checkpoint,
        path,
    )


def save_json(
    data: dict,
    path: Path,
) -> None:

    with open(
        path,
        "w",
        encoding="utf-8",
    ) as f:

        json.dump(
            data,
            f,
            indent=4,
        )


# ---------------------------------------------------------------------
# Main training function
# ---------------------------------------------------------------------

def train(
    data_dir: str | Path = DEFAULT_DATA_DIR,
    output_dir: str | Path = DEFAULT_OUTPUT_DIR,
    config: TrainingConfig | None = None,
) -> Dict:

    if config is None:
        config = TrainingConfig()

    set_seed(
        config.seed
    )

    data_dir = Path(data_dir)
    output_dir = Path(output_dir)

    output_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    # -------------------------------------------------------------
    # Device
    # -------------------------------------------------------------

    device = torch.device(
        "cuda"
        if torch.cuda.is_available()
        else "cpu"
    )

    print("=" * 70)
    print("ABNORMALITY MODEL TRAINING")
    print("=" * 70)

    print(
        f"Project root: {PROJECT_ROOT}"
    )

    print(
        f"Dataset:      {data_dir}"
    )

    print(
        f"Output:       {output_dir}"
    )

    print(
        f"Device:       {device}"
    )

    if torch.cuda.is_available():

        print(
            f"GPU:          "
            f"{torch.cuda.get_device_name(0)}"
        )

    print()

    # -------------------------------------------------------------
    # Dataset
    # -------------------------------------------------------------

    dataset = AbnormalityEmbeddingDataset(
        root_dir=data_dir,
        input_dim=config.input_dim,
    )

    print(
        f"Total samples: {len(dataset)}"
    )

    # -------------------------------------------------------------
    # Class distribution
    # -------------------------------------------------------------

    class_counts = {
        "normal": 0,
        "abnormal": 0,
    }

    for _, label in dataset.samples:

        if label == 0:
            class_counts["normal"] += 1
        else:
            class_counts["abnormal"] += 1

    print(
        f"Normal samples:    "
        f"{class_counts['normal']}"
    )

    print(
        f"Abnormal samples:  "
        f"{class_counts['abnormal']}"
    )

    # -------------------------------------------------------------
    # Train / validation split
    # -------------------------------------------------------------

    validation_size = int(
        len(dataset)
        * config.validation_split
    )

    train_size = (
        len(dataset)
        - validation_size
    )

    generator = torch.Generator().manual_seed(
        config.seed
    )

    train_dataset, validation_dataset = random_split(
        dataset,
        [
            train_size,
            validation_size,
        ],
        generator=generator,
    )

    print(
        f"Training samples:   "
        f"{len(train_dataset)}"
    )

    print(
        f"Validation samples: "
        f"{len(validation_dataset)}"
    )

    print()

    # -------------------------------------------------------------
    # DataLoaders
    # -------------------------------------------------------------

    train_loader = DataLoader(
        train_dataset,
        batch_size=config.batch_size,
        shuffle=True,
        num_workers=config.num_workers,
        pin_memory=torch.cuda.is_available(),
    )

    validation_loader = DataLoader(
        validation_dataset,
        batch_size=config.batch_size,
        shuffle=False,
        num_workers=config.num_workers,
        pin_memory=torch.cuda.is_available(),
    )

    # -------------------------------------------------------------
    # Model
    # -------------------------------------------------------------

    model = AbnormalityClassifier(
        input_dim=config.input_dim,
        hidden_dim=config.hidden_dim,
        num_classes=config.num_classes,
        dropout=config.dropout,
    ).to(device)

    # -------------------------------------------------------------
    # Class weights
    # -------------------------------------------------------------

    counts = torch.tensor(
        [
            class_counts["normal"],
            class_counts["abnormal"],
        ],
        dtype=torch.float32,
    )

    counts = torch.clamp(
        counts,
        min=1.0,
    )

    weights = (
        counts.sum()
        / (2.0 * counts)
    )

    weights = weights.to(device)

    criterion = nn.CrossEntropyLoss(
        weight=weights,
    )

    # -------------------------------------------------------------
    # Optimizer
    # -------------------------------------------------------------

    optimizer = torch.optim.AdamW(
        model.parameters(),
        lr=config.learning_rate,
        weight_decay=config.weight_decay,
    )

    scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(
        optimizer,
        mode="min",
        factor=0.5,
        patience=3,
    )

    # -------------------------------------------------------------
    # Parameter information
    # -------------------------------------------------------------

    total_parameters = sum(
        p.numel()
        for p in model.parameters()
    )

    trainable_parameters = sum(
        p.numel()
        for p in model.parameters()
        if p.requires_grad
    )

    print(
        f"Model parameters:          "
        f"{total_parameters:,}"
    )

    print(
        f"Trainable parameters:      "
        f"{trainable_parameters:,}"
    )

    print()

    # -------------------------------------------------------------
    # Training loop
    # -------------------------------------------------------------

    history = []

    best_validation_loss = float(
        "inf"
    )

    best_f1 = -1.0

    epochs_without_improvement = 0

    for epoch in range(
        1,
        config.epochs + 1,
    ):

        train_loss, train_metrics = train_one_epoch(
            model=model,
            loader=train_loader,
            criterion=criterion,
            optimizer=optimizer,
            device=device,
        )

        validation_loss, validation_metrics = validate(
            model=model,
            loader=validation_loader,
            criterion=criterion,
            device=device,
        )

        scheduler.step(
            validation_loss
        )

        current_lr = optimizer.param_groups[0]["lr"]

        epoch_record = {
            "epoch": epoch,

            "learning_rate":
                current_lr,

            "train_loss":
                train_loss,

            "validation_loss":
                validation_loss,

            "train_accuracy":
                train_metrics["accuracy"],

            "train_precision":
                train_metrics["precision"],

            "train_recall":
                train_metrics["recall"],

            "train_f1":
                train_metrics["f1"],

            "validation_accuracy":
                validation_metrics["accuracy"],

            "validation_precision":
                validation_metrics["precision"],

            "validation_recall":
                validation_metrics["recall"],

            "validation_f1":
                validation_metrics["f1"],
        }

        history.append(
            epoch_record
        )

        print(
            f"Epoch "
            f"{epoch:03d}/{config.epochs} | "
            f"train loss: "
            f"{train_loss:.4f} | "
            f"val loss: "
            f"{validation_loss:.4f} | "
            f"val acc: "
            f"{validation_metrics['accuracy']:.4f} | "
            f"val F1: "
            f"{validation_metrics['f1']:.4f}"
        )

        # ---------------------------------------------------------
        # Best model
        # ---------------------------------------------------------

        if (
            validation_metrics["f1"]
            > best_f1
        ):

            best_f1 = (
                validation_metrics["f1"]
            )

            best_validation_loss = (
                validation_loss
            )

            epochs_without_improvement = 0

            save_checkpoint(
                model=model,
                optimizer=optimizer,
                epoch=epoch,
                metrics=validation_metrics,
                config=config,
                path=output_dir / "best_model.pt",
            )

        else:

            epochs_without_improvement += 1

        # ---------------------------------------------------------
        # Early stopping
        # ---------------------------------------------------------

        if (
            epochs_without_improvement
            >= config.early_stopping_patience
        ):

            print()
            print(
                "Early stopping triggered."
            )

            break

    # -------------------------------------------------------------
    # Save final model
    # -------------------------------------------------------------

    save_checkpoint(
        model=model,
        optimizer=optimizer,
        epoch=len(history),
        metrics=validation_metrics,
        config=config,
        path=output_dir / "last_model.pt",
    )

    # -------------------------------------------------------------
    # Save training history
    # -------------------------------------------------------------

    save_json(
        {
            "config":
                vars(config),

            "class_distribution":
                class_counts,

            "history":
                history,
        },
        output_dir / "training_history.json",
    )

    # -------------------------------------------------------------
    # Final metrics
    # -------------------------------------------------------------

    final_metrics = {
        "best_validation_loss":
            float(best_validation_loss),

        "best_validation_f1":
            float(best_f1),

        "final_validation_loss":
            float(validation_loss),

        "final_validation_accuracy":
            float(
                validation_metrics[
                    "accuracy"
                ]
            ),

        "final_validation_precision":
            float(
                validation_metrics[
                    "precision"
                ]
            ),

        "final_validation_recall":
            float(
                validation_metrics[
                    "recall"
                ]
            ),

        "final_validation_f1":
            float(
                validation_metrics[
                    "f1"
                ]
            ),
    }

    save_json(
        final_metrics,
        output_dir / "metrics.json",
    )

    # -------------------------------------------------------------
    # Summary
    # -------------------------------------------------------------

    print()
    print("=" * 70)
    print("TRAINING COMPLETE")
    print("=" * 70)

    print(
        f"Best validation F1: "
        f"{best_f1:.4f}"
    )

    print(
        f"Final validation accuracy: "
        f"{validation_metrics['accuracy']:.4f}"
    )

    print(
        f"Final validation precision: "
        f"{validation_metrics['precision']:.4f}"
    )

    print(
        f"Final validation recall: "
        f"{validation_metrics['recall']:.4f}"
    )

    print(
        f"Final validation F1: "
        f"{validation_metrics['f1']:.4f}"
    )

    print()
    print(
        f"Best model: "
        f"{output_dir / 'best_model.pt'}"
    )

    print(
        f"Last model: "
        f"{output_dir / 'last_model.pt'}"
    )

    print("=" * 70)

    return {
        "model": model,
        "history": history,
        "metrics": final_metrics,
    }


# ---------------------------------------------------------------------
# Command line interface
# ---------------------------------------------------------------------

def parse_args() -> argparse.Namespace:

    parser = argparse.ArgumentParser(
        description=(
            "Train the abnormality classification model."
        )
    )

    parser.add_argument(
        "--data",
        type=str,
        default=str(DEFAULT_DATA_DIR),
        help="Path to abnormality embedding dataset.",
    )

    parser.add_argument(
        "--output",
        type=str,
        default=str(DEFAULT_OUTPUT_DIR),
        help="Directory for training outputs.",
    )

    parser.add_argument(
        "--epochs",
        type=int,
        default=30,
        help="Number of training epochs.",
    )

    parser.add_argument(
        "--batch-size",
        type=int,
        default=32,
        help="Training batch size.",
    )

    parser.add_argument(
        "--learning-rate",
        type=float,
        default=1e-4,
        help="Learning rate.",
    )

    parser.add_argument(
        "--input-dim",
        type=int,
        default=768,
        help="Input embedding dimension.",
    )

    parser.add_argument(
        "--hidden-dim",
        type=int,
        default=512,
        help="Hidden layer dimension.",
    )

    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed.",
    )

    return parser.parse_args()


# ---------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------

def main() -> None:

    args = parse_args()

    config = TrainingConfig(
        input_dim=args.input_dim,
        hidden_dim=args.hidden_dim,
        epochs=args.epochs,
        batch_size=args.batch_size,
        learning_rate=args.learning_rate,
        seed=args.seed,
    )

    train(
        data_dir=args.data,
        output_dir=args.output,
        config=config,
    )


if __name__ == "__main__":
    main()