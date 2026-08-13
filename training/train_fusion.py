"""
training/train_fusion.py

Training pipeline for the multimodal fusion model.

The goal is to learn a shared representation from multiple biological
modalities, for example:

    image / DINOv2 embeddings
    cell / Cellpose-derived features
    RNA / Scanpy-derived features
    hand / MANO or MediaPipe-derived features

Expected input:
    data/processed/embeddings/fusion_features.csv

Required columns:
    subject_id
    target

All remaining numeric columns are treated as modality features.

Recommended naming convention:

    image_000 ... image_767
    cell_000  ... cell_127
    rna_000   ... rna_255
    hand_000  ... hand_127

The model:
    1. Loads multimodal feature data.
    2. Detects feature groups by column prefix.
    3. Splits data by subject.
    4. Standardizes each modality using training statistics only.
    5. Projects each modality into a common latent space.
    6. Fuses modalities with attention/gating.
    7. Produces:
         - fused embedding
         - prediction
    8. Trains using supervised regression.
    9. Saves the best model checkpoint.
   10. Saves training history and metadata.

This module is intended for research and model-development purposes.
It does not provide clinical diagnosis or treatment recommendations.
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
    Set random seeds for reproducibility.
    """

    random.seed(seed)
    np.random.seed(seed)

    torch.manual_seed(seed)

    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)

    torch.backends.cudnn.deterministic = True
    torch.backends.cudnn.benchmark = False


# ============================================================
# Configuration
# ============================================================

@dataclass
class FusionTrainingConfig:
    """
    Configuration for multimodal fusion training.
    """

    input_csv: str = (
        "data/processed/embeddings/"
        "fusion_features.csv"
    )

    output_dir: str = (
        "outputs/embeddings/fusion"
    )

    subject_column: str = "subject_id"

    target_column: str = "target"

    # Feature prefixes.
    image_prefix: str = "image_"
    cell_prefix: str = "cell_"
    rna_prefix: str = "rna_"
    hand_prefix: str = "hand_"

    # Latent dimensions.
    modality_dim: int = 128
    fusion_dim: int = 256

    # Network.
    dropout: float = 0.20

    # Training.
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

    # Missing-modality handling.
    allow_missing_modalities: bool = True


# ============================================================
# Device
# ============================================================

def resolve_device(
    requested: str,
) -> torch.device:

    if requested == "auto":

        if torch.cuda.is_available():
            return torch.device("cuda")

        if (
            getattr(
                torch.backends,
                "mps",
                None,
            )
            is not None
        ):

            if torch.backends.mps.is_available():
                return torch.device("mps")

        return torch.device("cpu")

    return torch.device(requested)


# ============================================================
# Dataset
# ============================================================

class FusionDataset(Dataset):
    """
    Dataset containing four possible modalities.

    Modalities:
        image
        cell
        rna
        hand

    Missing modalities are represented by zero vectors.
    A modality mask indicates which modalities are actually present.
    """

    def __init__(
        self,
        image: np.ndarray,
        cell: np.ndarray,
        rna: np.ndarray,
        hand: np.ndarray,
        modality_mask: np.ndarray,
        targets: np.ndarray,
    ) -> None:

        self.image = torch.tensor(
            image,
            dtype=torch.float32,
        )

        self.cell = torch.tensor(
            cell,
            dtype=torch.float32,
        )

        self.rna = torch.tensor(
            rna,
            dtype=torch.float32,
        )

        self.hand = torch.tensor(
            hand,
            dtype=torch.float32,
        )

        self.modality_mask = torch.tensor(
            modality_mask,
            dtype=torch.float32,
        )

        self.targets = torch.tensor(
            targets,
            dtype=torch.float32,
        )

        n = len(self.targets)

        for array_name, array in [
            ("image", self.image),
            ("cell", self.cell),
            ("rna", self.rna),
            ("hand", self.hand),
            ("modality_mask", self.modality_mask),
        ]:

            if len(array) != n:
                raise ValueError(
                    f"{array_name} has "
                    f"{len(array)} samples, expected {n}."
                )

    def __len__(self) -> int:
        return len(self.targets)

    def __getitem__(
        self,
        index: int,
    ) -> Dict[str, torch.Tensor]:

        return {
            "image": self.image[index],
            "cell": self.cell[index],
            "rna": self.rna[index],
            "hand": self.hand[index],
            "modality_mask": self.modality_mask[index],
            "target": self.targets[index],
        }


# ============================================================
# Modality projector
# ============================================================

class ModalityProjector(nn.Module):
    """
    Projects one modality into a common latent dimension.
    """

    def __init__(
        self,
        input_dim: int,
        latent_dim: int,
        dropout: float,
    ) -> None:

        super().__init__()

        self.network = nn.Sequential(
            nn.Linear(
                input_dim,
                latent_dim,
            ),
            nn.LayerNorm(
                latent_dim
            ),
            nn.GELU(),
            nn.Dropout(
                dropout
            ),
        )

    def forward(
        self,
        x: torch.Tensor,
    ) -> torch.Tensor:

        return self.network(x)


# ============================================================
# Multimodal fusion model
# ============================================================

class MultimodalFusionModel(nn.Module):
    """
    Multimodal fusion network.

    Each modality is first projected into the same latent space.

    Then a learned attention/gating mechanism determines the relative
    contribution of each available modality.

    Outputs:
        fused_embedding
        prediction
    """

    MODALITIES = (
        "image",
        "cell",
        "rna",
        "hand",
    )

    def __init__(
        self,
        image_dim: int,
        cell_dim: int,
        rna_dim: int,
        hand_dim: int,
        modality_dim: int = 128,
        fusion_dim: int = 256,
        dropout: float = 0.20,
    ) -> None:

        super().__init__()

        self.image_projector = (
            ModalityProjector(
                image_dim,
                modality_dim,
                dropout,
            )
        )

        self.cell_projector = (
            ModalityProjector(
                cell_dim,
                modality_dim,
                dropout,
            )
        )

        self.rna_projector = (
            ModalityProjector(
                rna_dim,
                modality_dim,
                dropout,
            )
        )

        self.hand_projector = (
            ModalityProjector(
                hand_dim,
                modality_dim,
                dropout,
            )
        )

        self.attention = nn.Sequential(
            nn.Linear(
                modality_dim,
                modality_dim // 2,
            ),
            nn.GELU(),
            nn.Linear(
                modality_dim // 2,
                1,
            ),
        )

        self.fusion = nn.Sequential(
            nn.Linear(
                modality_dim,
                fusion_dim,
            ),
            nn.LayerNorm(
                fusion_dim
            ),
            nn.GELU(),
            nn.Dropout(
                dropout
            ),
        )

        self.head = nn.Sequential(
            nn.Linear(
                fusion_dim,
                fusion_dim // 2,
            ),
            nn.GELU(),
            nn.Dropout(
                dropout
            ),
            nn.Linear(
                fusion_dim // 2,
                1,
            ),
        )

    def forward(
        self,
        image: torch.Tensor,
        cell: torch.Tensor,
        rna: torch.Tensor,
        hand: torch.Tensor,
        modality_mask: torch.Tensor,
    ) -> Tuple[
        torch.Tensor,
        torch.Tensor,
        torch.Tensor,
    ]:

        # ----------------------------------------------------
        # Project modalities
        # ----------------------------------------------------

        image_z = self.image_projector(
            image
        )

        cell_z = self.cell_projector(
            cell
        )

        rna_z = self.rna_projector(
            rna
        )

        hand_z = self.hand_projector(
            hand
        )

        # [batch, modalities, latent]
        modality_stack = torch.stack(
            [
                image_z,
                cell_z,
                rna_z,
                hand_z,
            ],
            dim=1,
        )

        # ----------------------------------------------------
        # Attention scores
        # ----------------------------------------------------

        scores = self.attention(
            modality_stack
        ).squeeze(-1)

        # Missing modalities cannot participate.
        available = modality_mask > 0

        scores = scores.masked_fill(
            ~available,
            -1e9,
        )

        attention_weights = torch.softmax(
            scores,
            dim=1,
        )

        # ----------------------------------------------------
        # Weighted fusion
        # ----------------------------------------------------

        weighted = (
            modality_stack
            * attention_weights.unsqueeze(-1)
        )

        fused = weighted.sum(
            dim=1
        )

        fused_embedding = self.fusion(
            fused
        )

        prediction = self.head(
            fused_embedding
        ).squeeze(-1)

        return (
            prediction,
            fused_embedding,
            attention_weights,
        )


# ============================================================
# Metrics
# ============================================================

def mae(
    predictions: np.ndarray,
    targets: np.ndarray,
) -> float:

    return float(
        np.mean(
            np.abs(
                predictions - targets
            )
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
# Data loading
# ============================================================

def load_dataframe(
    path: Path,
    subject_column: str,
    target_column: str,
) -> pd.DataFrame:

    if not path.exists():

        raise FileNotFoundError(
            f"Fusion training file not found: {path}"
        )

    df = pd.read_csv(
        path
    )

    if df.empty:

        raise ValueError(
            "Fusion training dataset is empty."
        )

    required = [
        subject_column,
        target_column,
    ]

    missing = [
        column
        for column in required
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
            "At least 10 valid samples are required."
        )

    return df


# ============================================================
# Feature detection
# ============================================================

def get_feature_columns(
    df: pd.DataFrame,
    prefix: str,
) -> List[str]:

    columns = [
        column
        for column in df.columns
        if column.startswith(prefix)
    ]

    return columns


def detect_modalities(
    df: pd.DataFrame,
    config: FusionTrainingConfig,
) -> Dict[str, List[str]]:

    modalities = {

        "image": get_feature_columns(
            df,
            config.image_prefix,
        ),

        "cell": get_feature_columns(
            df,
            config.cell_prefix,
        ),

        "rna": get_feature_columns(
            df,
            config.rna_prefix,
        ),

        "hand": get_feature_columns(
            df,
            config.hand_prefix,
        ),
    }

    print()
    print("Detected modalities:")

    for name, columns in modalities.items():

        print(
            f"  {name:>5}: "
            f"{len(columns)} features"
        )

    if not any(
        len(columns) > 0
        for columns in modalities.values()
    ):

        raise ValueError(
            "No modality features detected."
        )

    return modalities


# ============================================================
# Subject split
# ============================================================

def split_subjects(
    df: pd.DataFrame,
    subject_column: str,
    validation_fraction: float,
    test_fraction: float,
    seed: int,
) -> Tuple[
    pd.DataFrame,
    pd.DataFrame,
    pd.DataFrame,
]:

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

    rng = np.random.default_rng(
        seed
    )

    rng.shuffle(
        subjects
    )

    n = len(subjects)

    n_test = max(
        1,
        int(
            round(
                n * test_fraction
            )
        ),
    )

    n_val = max(
        1,
        int(
            round(
                n * validation_fraction
            )
        ),
    )

    if n_test + n_val >= n:

        n_test = 1
        n_val = 1

    test_subjects = set(
        subjects[:n_test]
    )

    val_subjects = set(
        subjects[
            n_test:n_test + n_val
        ]
    )

    train_subjects = set(
        subjects[
            n_test + n_val:
        ]
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

def prepare_numeric_features(
    df: pd.DataFrame,
    columns: List[str],
) -> pd.DataFrame:

    if not columns:

        return pd.DataFrame(
            index=df.index
        )

    features = df[
        columns
    ].copy()

    for column in columns:

        features[column] = pd.to_numeric(
            features[column],
            errors="coerce",
        )

    features = features.replace(
        [np.inf, -np.inf],
        np.nan,
    )

    return features


def fit_modality_statistics(
    features: pd.DataFrame,
) -> Dict[str, Dict[str, float]]:

    if features.empty:

        return {
            "mean": {},
            "std": {},
        }

    medians = features.median()

    features = features.fillna(
        medians
    )

    means = features.mean()

    stds = features.std(
        ddof=0
    )

    stds = stds.replace(
        0,
        1.0,
    )

    return {
        "mean": {
            key: float(value)
            for key, value in means.items()
        },
        "std": {
            key: float(value)
            for key, value in stds.items()
        },
        "median": {
            key: float(value)
            for key, value in medians.items()
        },
    }


def apply_modality_statistics(
    features: pd.DataFrame,
    statistics: Dict[str, Dict[str, float]],
) -> np.ndarray:

    if features.empty:

        return np.zeros(
            (len(features), 1),
            dtype=np.float32,
        )

    means = statistics["mean"]
    stds = statistics["std"]
    medians = statistics.get(
        "median",
        {},
    )

    features = features.copy()

    for column in features.columns:

        median = medians.get(
            column,
            0.0,
        )

        features[column] = (
            features[column]
            .fillna(median)
        )

        features[column] = (
            features[column]
            - means[column]
        ) / stds[column]

    return features.to_numpy(
        dtype=np.float32
    )


# ============================================================
# Modality matrix preparation
# ============================================================

def prepare_modality_matrix(
    train_df: pd.DataFrame,
    val_df: pd.DataFrame,
    test_df: pd.DataFrame,
    feature_columns: List[str],
) -> Tuple[
    np.ndarray,
    np.ndarray,
    np.ndarray,
    Dict[str, Dict[str, float]],
]:

    if not feature_columns:

        # Missing modality.
        return (
            np.zeros(
                (len(train_df), 1),
                dtype=np.float32,
            ),
            np.zeros(
                (len(val_df), 1),
                dtype=np.float32,
            ),
            np.zeros(
                (len(test_df), 1),
                dtype=np.float32,
            ),
            {
                "mean": {},
                "std": {},
                "median": {},
            },
        )

    train_features = prepare_numeric_features(
        train_df,
        feature_columns,
    )

    val_features = prepare_numeric_features(
        val_df,
        feature_columns,
    )

    test_features = prepare_numeric_features(
        test_df,
        feature_columns,
    )

    statistics = fit_modality_statistics(
        train_features
    )

    X_train = apply_modality_statistics(
        train_features,
        statistics,
    )

    X_val = apply_modality_statistics(
        val_features,
        statistics,
    )

    X_test = apply_modality_statistics(
        test_features,
        statistics,
    )

    return (
        X_train,
        X_val,
        X_test,
        statistics,
    )


# ============================================================
# Modality availability
# ============================================================

def modality_availability(
    df: pd.DataFrame,
    feature_columns: List[str],
) -> np.ndarray:

    if not feature_columns:

        return np.zeros(
            len(df),
            dtype=np.float32,
        )

    values = (
        df[feature_columns]
        .apply(
            pd.to_numeric,
            errors="coerce",
        )
    )

    available = (
        values.notna()
        .any(axis=1)
    )

    return available.to_numpy(
        dtype=np.float32
    )


def build_modality_mask(
    df: pd.DataFrame,
    modalities: Dict[str, List[str]],
) -> np.ndarray:

    masks = []

    for name in [
        "image",
        "cell",
        "rna",
        "hand",
    ]:

        masks.append(
            modality_availability(
                df,
                modalities[name],
            )
        )

    return np.stack(
        masks,
        axis=1,
    ).astype(
        np.float32
    )


# ============================================================
# Training
# ============================================================

def train_one_epoch(
    model: MultimodalFusionModel,
    loader: DataLoader,
    optimizer: torch.optim.Optimizer,
    criterion: nn.Module,
    device: torch.device,
) -> float:

    model.train()

    total_loss = 0.0
    total_samples = 0

    for batch in loader:

        image = batch["image"].to(
            device
        )

        cell = batch["cell"].to(
            device
        )

        rna = batch["rna"].to(
            device
        )

        hand = batch["hand"].to(
            device
        )

        modality_mask = batch[
            "modality_mask"
        ].to(device)

        targets = batch[
            "target"
        ].to(device)

        optimizer.zero_grad(
            set_to_none=True
        )

        predictions, _, _ = model(
            image=image,
            cell=cell,
            rna=rna,
            hand=hand,
            modality_mask=modality_mask,
        )

        loss = criterion(
            predictions,
            targets,
        )

        loss.backward()

        optimizer.step()

        batch_size = (
            targets.size(0)
        )

        total_loss += (
            loss.item()
            * batch_size
        )

        total_samples += batch_size

    return total_loss / max(
        total_samples,
        1,
    )


# ============================================================
# Evaluation
# ============================================================

@torch.no_grad()
def evaluate(
    model: MultimodalFusionModel,
    loader: DataLoader,
    criterion: nn.Module,
    device: torch.device,
) -> Dict[str, object]:

    model.eval()

    total_loss = 0.0
    total_samples = 0

    predictions = []
    targets = []
    attentions = []

    for batch in loader:

        image = batch["image"].to(
            device
        )

        cell = batch["cell"].to(
            device
        )

        rna = batch["rna"].to(
            device
        )

        hand = batch["hand"].to(
            device
        )

        modality_mask = batch[
            "modality_mask"
        ].to(device)

        batch_targets = batch[
            "target"
        ].to(device)

        (
            batch_predictions,
            _,
            batch_attention,
        ) = model(
            image=image,
            cell=cell,
            rna=rna,
            hand=hand,
            modality_mask=modality_mask,
        )

        loss = criterion(
            batch_predictions,
            batch_targets,
        )

        batch_size = (
            batch_targets.size(0)
        )

        total_loss += (
            loss.item()
            * batch_size
        )

        total_samples += batch_size

        predictions.append(
            batch_predictions
            .cpu()
            .numpy()
        )

        targets.append(
            batch_targets
            .cpu()
            .numpy()
        )

        attentions.append(
            batch_attention
            .cpu()
            .numpy()
        )

    predictions_np = np.concatenate(
        predictions
    )

    targets_np = np.concatenate(
        targets
    )

    attention_np = np.concatenate(
        attentions
    )

    return {
        "loss": float(
            total_loss
            / max(
                total_samples,
                1,
            )
        ),
        "mae": mae(
            predictions_np,
            targets_np,
        ),
        "rmse": rmse(
            predictions_np,
            targets_np,
        ),
        "r2": r2_score(
            predictions_np,
            targets_np,
        ),
        "attention_mean": (
            attention_np.mean(
                axis=0
            ).tolist()
        ),
    }


# ============================================================
# Checkpoint
# ============================================================

def save_checkpoint(
    path: Path,
    model: MultimodalFusionModel,
    optimizer: torch.optim.Optimizer,
    epoch: int,
    metrics: Dict[str, object],
    config: FusionTrainingConfig,
    modalities: Dict[str, List[str]],
    statistics: Dict[str, Dict],
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
            asdict(config),

        "modalities":
            modalities,

        "statistics":
            statistics,
    }

    torch.save(
        checkpoint,
        path,
    )


# ============================================================
# Main training function
# ============================================================

def train_fusion_model(
    config: FusionTrainingConfig,
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

    print("=" * 70)
    print("MULTIMODAL FUSION MODEL TRAINING")
    print("=" * 70)

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
    # Load dataset
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
    # Detect modalities
    # --------------------------------------------------------

    modalities = detect_modalities(
        df,
        config,
    )

    # --------------------------------------------------------
    # Split by subject
    # --------------------------------------------------------

    (
        train_df,
        val_df,
        test_df,
    ) = split_subjects(
        df,
        config.subject_column,
        config.validation_fraction,
        config.test_fraction,
        config.seed,
    )

    print()
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
    # Prepare modality matrices
    # --------------------------------------------------------

    matrices = {}

    statistics = {}

    for modality_name in [
        "image",
        "cell",
        "rna",
        "hand",
    ]:

        (
            X_train,
            X_val,
            X_test,
            modality_statistics,
        ) = prepare_modality_matrix(
            train_df,
            val_df,
            test_df,
            modalities[modality_name],
        )

        matrices[
            modality_name
        ] = {
            "train": X_train,
            "val": X_val,
            "test": X_test,
        }

        statistics[
            modality_name
        ] = modality_statistics

    # --------------------------------------------------------
    # Modality masks
    # --------------------------------------------------------

    train_mask = build_modality_mask(
        train_df,
        modalities,
    )

    val_mask = build_modality_mask(
        val_df,
        modalities,
    )

    test_mask = build_modality_mask(
        test_df,
        modalities,
    )

    # If missing modalities are not allowed, verify data.
    if not config.allow_missing_modalities:

        if np.any(train_mask == 0):

            raise ValueError(
                "Missing modalities found in training data."
            )

        if np.any(val_mask == 0):

            raise ValueError(
                "Missing modalities found in validation data."
            )

        if np.any(test_mask == 0):

            raise ValueError(
                "Missing modalities found in test data."
            )

    # --------------------------------------------------------
    # Targets
    # --------------------------------------------------------

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
    # Create datasets
    # --------------------------------------------------------

    train_dataset = FusionDataset(
        matrices["image"]["train"],
        matrices["cell"]["train"],
        matrices["rna"]["train"],
        matrices["hand"]["train"],
        train_mask,
        y_train,
    )

    val_dataset = FusionDataset(
        matrices["image"]["val"],
        matrices["cell"]["val"],
        matrices["rna"]["val"],
        matrices["hand"]["val"],
        val_mask,
        y_val,
    )

    test_dataset = FusionDataset(
        matrices["image"]["test"],
        matrices["cell"]["test"],
        matrices["rna"]["test"],
        matrices["hand"]["test"],
        test_mask,
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
    # Input dimensions
    # --------------------------------------------------------

    image_dim = matrices[
        "image"
    ]["train"].shape[1]

    cell_dim = matrices[
        "cell"
    ]["train"].shape[1]

    rna_dim = matrices[
        "rna"
    ]["train"].shape[1]

    hand_dim = matrices[
        "hand"
    ]["train"].shape[1]

    print()
    print("Input dimensions:")

    print(
        f"  image: {image_dim}"
    )

    print(
        f"   cell: {cell_dim}"
    )

    print(
        f"    rna: {rna_dim}"
    )

    print(
        f"   hand: {hand_dim}"
    )

    # --------------------------------------------------------
    # Model
    # --------------------------------------------------------

    model = MultimodalFusionModel(
        image_dim=image_dim,
        cell_dim=cell_dim,
        rna_dim=rna_dim,
        hand_dim=hand_dim,
        modality_dim=config.modality_dim,
        fusion_dim=config.fusion_dim,
        dropout=config.dropout,
    ).to(device)

    parameter_count = sum(
        parameter.numel()
        for parameter in model.parameters()
    )

    print()
    print(
        f"Model parameters: {parameter_count:,}"
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
    # Training
    # --------------------------------------------------------

    best_val_mae = float(
        "inf"
    )

    best_epoch = 0

    patience_counter = 0

    history = []

    checkpoint_path = (
        output_dir
        / "fusion_model_best.pt"
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

        attention = (
            val_metrics[
                "attention_mean"
            ]
        )

        history_record = {
            "epoch": epoch,

            "train_loss":
                train_loss,

            "val_loss":
                val_metrics["loss"],

            "val_mae":
                val_metrics["mae"],

            "val_rmse":
                val_metrics["rmse"],

            "val_r2":
                val_metrics["r2"],

            "attention_image":
                attention[0],

            "attention_cell":
                attention[1],

            "attention_rna":
                attention[2],

            "attention_hand":
                attention[3],
        }

        history.append(
            history_record
        )

        print(
            f"Epoch {epoch:03d} | "
            f"train_loss={train_loss:.4f} | "
            f"val_MAE={val_metrics['mae']:.3f} | "
            f"val_RMSE={val_metrics['rmse']:.3f} | "
            f"val_R2={val_metrics['r2']:.3f} | "
            f"attention="
            f"[{attention[0]:.2f}, "
            f"{attention[1]:.2f}, "
            f"{attention[2]:.2f}, "
            f"{attention[3]:.2f}]"
        )

        # ----------------------------------------------------
        # Best checkpoint
        # ----------------------------------------------------

        if (
            val_metrics["mae"]
            < best_val_mae
        ):

            best_val_mae = (
                val_metrics["mae"]
            )

            best_epoch = epoch

            patience_counter = 0

            save_checkpoint(
                checkpoint_path,
                model,
                optimizer,
                epoch,
                val_metrics,
                config,
                modalities,
                statistics,
            )

        else:

            patience_counter += 1

        # ----------------------------------------------------
        # Early stopping
        # ----------------------------------------------------

        if (
            patience_counter
            >= config.patience
        ):

            print()
            print(
                "Early stopping."
            )

            break

    # --------------------------------------------------------
    # Save history
    # --------------------------------------------------------

    history_path = (
        output_dir
        / "fusion_training_history.csv"
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
    # Test
    # --------------------------------------------------------

    test_metrics = evaluate(
        model,
        test_loader,
        criterion,
        device,
    )

    print()
    print("=" * 70)
    print("FINAL FUSION MODEL RESULTS")
    print("=" * 70)

    print(
        f"MAE:  {test_metrics['mae']:.4f}"
    )

    print(
        f"RMSE: {test_metrics['rmse']:.4f}"
    )

    print(
        f"R²:   {test_metrics['r2']:.4f}"
    )

    attention = (
        test_metrics[
            "attention_mean"
        ]
    )

    print()
    print(
        "Average modality contribution:"
    )

    print(
        f"  image: {attention[0]:.3f}"
    )

    print(
        f"   cell: {attention[1]:.3f}"
    )

    print(
        f"    rna: {attention[2]:.3f}"
    )

    print(
        f"   hand: {attention[3]:.3f}"
    )

    # --------------------------------------------------------
    # Metadata
    # --------------------------------------------------------

    metadata = {

        "task":
            "multimodal_fusion",

        "input_csv":
            str(input_path),

        "num_samples":
            int(len(df)),

        "num_subjects":
            int(
                df[
                    config.subject_column
                ].nunique()
            ),

        "modalities":
            {
                name: len(columns)
                for name, columns
                in modalities.items()
            },

        "model_parameters":
            int(parameter_count),

        "best_epoch":
            int(best_epoch),

        "best_validation_mae":
            float(best_val_mae),

        "test_metrics":
            test_metrics,

        "device":
            str(device),

        "config":
            asdict(config),
    }

    metadata_path = (
        output_dir
        / "fusion_training_metadata.json"
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
        "Multimodal fusion training complete."
    )

    return {
        "model": model,
        "checkpoint": checkpoint_path,
        "history": history,
        "test_metrics": test_metrics,
        "modalities": modalities,
        "statistics": statistics,
    }


# ============================================================
# CLI
# ============================================================

def build_parser() -> argparse.ArgumentParser:

    parser = argparse.ArgumentParser(
        description=(
            "Train multimodal fusion model."
        )
    )

    parser.add_argument(
        "--input",
        default=(
            "data/processed/embeddings/"
            "fusion_features.csv"
        ),
        help=(
            "Input CSV containing "
            "multimodal features."
        ),
    )

    parser.add_argument(
        "--output",
        default=(
            "outputs/embeddings/fusion"
        ),
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
        "--modality-dim",
        type=int,
        default=128,
    )

    parser.add_argument(
        "--fusion-dim",
        type=int,
        default=256,
    )

    parser.add_argument(
        "--dropout",
        type=float,
        default=0.20,
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


# ============================================================
# Entry point
# ============================================================

def main() -> None:

    parser = build_parser()

    args = parser.parse_args()

    config = FusionTrainingConfig(
        input_csv=args.input,
        output_dir=args.output,
        epochs=args.epochs,
        batch_size=args.batch_size,
        learning_rate=args.learning_rate,
        modality_dim=args.modality_dim,
        fusion_dim=args.fusion_dim,
        dropout=args.dropout,
        patience=args.patience,
        seed=args.seed,
        device=args.device,
    )

    train_fusion_model(
        config
    )


if __name__ == "__main__":
    main()