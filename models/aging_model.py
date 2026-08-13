"""
aging_model.py

Model predykcyjny starzenia skóry.

Odpowiedzialność modułu:
    - łączenie cech multimodalnych związanych ze starzeniem,
    - predykcja wieku biologicznego / skóry,
    - generowanie embeddingu starzenia,
    - estymacja niepewności predykcji,
    - możliwość wykorzystania modelu jako części większego pipeline'u.

Model nie wykonuje:
    - preprocessingu obrazów,
    - segmentacji,
    - analizy RNA,
    - detekcji komórek,
    - ekstrakcji cech DINOv2.

Te zadania powinny być wykonywane przez odpowiednie moduły
pipeline/ oraz models/.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Mapping, Optional, Sequence, Tuple, Union

import torch
import torch.nn as nn
import torch.nn.functional as F


TensorLike = Union[torch.Tensor, Sequence[float]]


# ============================================================================
# Configuration
# ============================================================================


@dataclass
class AgingModelConfig:
    """
    Konfiguracja modelu starzenia.

    Parametry:
        image_dim:
            Wymiar embeddingu obrazu, np. DINOv2.

        cell_dim:
            Wymiar embeddingu cech komórkowych.

        rna_dim:
            Wymiar embeddingu RNA.

        morphology_dim:
            Wymiar cech morfologicznych.

        hand_dim:
            Wymiar embeddingu dłoni, jeśli jest wykorzystywany.

        hidden_dim:
            Wymiar warstwy ukrytej.

        aging_embedding_dim:
            Wymiar końcowego embeddingu starzenia.

        dropout:
            Dropout stosowany w głowach predykcyjnych.

        min_age:
            Minimalny wiek przewidywany przez model.

        max_age:
            Maksymalny wiek przewidywany przez model.
    """

    image_dim: int = 768
    cell_dim: int = 256
    rna_dim: int = 256
    morphology_dim: int = 128
    hand_dim: int = 128

    hidden_dim: int = 512
    aging_embedding_dim: int = 256

    dropout: float = 0.2

    min_age: float = 0.0
    max_age: float = 120.0


# ============================================================================
# Output
# ============================================================================


@dataclass
class AgingPrediction:
    """
    Wynik predykcji modelu starzenia.
    """

    predicted_age: torch.Tensor
    aging_score: torch.Tensor
    aging_embedding: torch.Tensor
    confidence: torch.Tensor

    # Opcjonalne wartości pomocnicze.
    age_uncertainty: Optional[torch.Tensor] = None

    # Surowe reprezentacje multimodalne.
    fused_features: Optional[torch.Tensor] = None

    def to_dict(self) -> Dict[str, torch.Tensor]:
        """
        Konwersja wyniku do słownika.
        """

        result = {
            "predicted_age": self.predicted_age,
            "aging_score": self.aging_score,
            "aging_embedding": self.aging_embedding,
            "confidence": self.confidence,
        }

        if self.age_uncertainty is not None:
            result["age_uncertainty"] = self.age_uncertainty

        if self.fused_features is not None:
            result["fused_features"] = self.fused_features

        return result


# ============================================================================
# Utility modules
# ============================================================================


class MLPBlock(nn.Module):
    """
    Standardowy blok MLP:

        Linear
        -> LayerNorm
        -> GELU
        -> Dropout
        -> Linear
        -> LayerNorm
        -> GELU
    """

    def __init__(
        self,
        input_dim: int,
        hidden_dim: int,
        output_dim: int,
        dropout: float = 0.2,
    ) -> None:
        super().__init__()

        self.net = nn.Sequential(
            nn.Linear(input_dim, hidden_dim),
            nn.LayerNorm(hidden_dim),
            nn.GELU(),
            nn.Dropout(dropout),

            nn.Linear(hidden_dim, output_dim),
            nn.LayerNorm(output_dim),
            nn.GELU(),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.net(x)


class FeatureEncoder(nn.Module):
    """
    Encoder pojedynczego źródła danych.

    Pozwala sprowadzić różne modalności do wspólnej przestrzeni.
    """

    def __init__(
        self,
        input_dim: int,
        embedding_dim: int,
        dropout: float = 0.2,
    ) -> None:
        super().__init__()

        self.input_dim = input_dim
        self.embedding_dim = embedding_dim

        self.encoder = nn.Sequential(
            nn.Linear(input_dim, embedding_dim),
            nn.LayerNorm(embedding_dim),
            nn.GELU(),
            nn.Dropout(dropout),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.encoder(x)


# ============================================================================
# Main model
# ============================================================================


class AgingModel(nn.Module):
    """
    Multimodalny model predykcji starzenia.

    Model może korzystać z:

        image
            ↓
        DINOv2 embedding

        cells
            ↓
        CellPose / cell-level features

        rna
            ↓
        RNA / Scanpy embedding

        morphology
            ↓
        handcrafted / learned morphology features

        hand
            ↓
        MANO / hand embedding

        Wszystkie modalności
            ↓
        fusion
            ↓
        aging representation
            ↓
        ┌───────────────┬──────────────┐
        ↓               ↓              ↓
      age           aging score     confidence

    Główna predykcja:
        predicted_age

    Dodatkowo:
        aging_embedding
        aging_score
        confidence
    """

    def __init__(
        self,
        config: Optional[AgingModelConfig] = None,
    ) -> None:
        super().__init__()

        self.config = config or AgingModelConfig()

        cfg = self.config

        # ------------------------------------------------------------------
        # Encoders
        # ------------------------------------------------------------------

        self.image_encoder = FeatureEncoder(
            input_dim=cfg.image_dim,
            embedding_dim=cfg.hidden_dim,
            dropout=cfg.dropout,
        )

        self.cell_encoder = FeatureEncoder(
            input_dim=cfg.cell_dim,
            embedding_dim=cfg.hidden_dim,
            dropout=cfg.dropout,
        )

        self.rna_encoder = FeatureEncoder(
            input_dim=cfg.rna_dim,
            embedding_dim=cfg.hidden_dim,
            dropout=cfg.dropout,
        )

        self.morphology_encoder = FeatureEncoder(
            input_dim=cfg.morphology_dim,
            embedding_dim=cfg.hidden_dim,
            dropout=cfg.dropout,
        )

        self.hand_encoder = FeatureEncoder(
            input_dim=cfg.hand_dim,
            embedding_dim=cfg.hidden_dim,
            dropout=cfg.dropout,
        )

        # ------------------------------------------------------------------
        # Fusion
        # ------------------------------------------------------------------

        num_modalities = 5

        fusion_input_dim = cfg.hidden_dim * num_modalities

        self.fusion = MLPBlock(
            input_dim=fusion_input_dim,
            hidden_dim=cfg.hidden_dim,
            output_dim=cfg.hidden_dim,
            dropout=cfg.dropout,
        )

        # ------------------------------------------------------------------
        # Aging representation
        # ------------------------------------------------------------------

        self.aging_representation = nn.Sequential(
            nn.Linear(cfg.hidden_dim, cfg.hidden_dim),
            nn.LayerNorm(cfg.hidden_dim),
            nn.GELU(),
            nn.Dropout(cfg.dropout),

            nn.Linear(
                cfg.hidden_dim,
                cfg.aging_embedding_dim,
            ),
            nn.LayerNorm(cfg.aging_embedding_dim),
        )

        # ------------------------------------------------------------------
        # Age prediction head
        # ------------------------------------------------------------------

        self.age_head = nn.Sequential(
            nn.Linear(
                cfg.aging_embedding_dim,
                cfg.hidden_dim // 2,
            ),
            nn.GELU(),
            nn.Dropout(cfg.dropout),

            nn.Linear(
                cfg.hidden_dim // 2,
                1,
            ),
        )

        # ------------------------------------------------------------------
        # Aging score head
        # ------------------------------------------------------------------

        self.aging_score_head = nn.Sequential(
            nn.Linear(
                cfg.aging_embedding_dim,
                cfg.hidden_dim // 2,
            ),
            nn.GELU(),
            nn.Dropout(cfg.dropout),

            nn.Linear(
                cfg.hidden_dim // 2,
                1,
            ),
            nn.Sigmoid(),
        )

        # ------------------------------------------------------------------
        # Uncertainty head
        # ------------------------------------------------------------------

        self.uncertainty_head = nn.Sequential(
            nn.Linear(
                cfg.aging_embedding_dim,
                cfg.hidden_dim // 2,
            ),
            nn.GELU(),
            nn.Dropout(cfg.dropout),

            nn.Linear(
                cfg.hidden_dim // 2,
                1,
            ),
            nn.Softplus(),
        )

    # ======================================================================
    # Input preparation
    # ======================================================================

    @staticmethod
    def _ensure_tensor(
        x: Optional[TensorLike],
        *,
        device: torch.device,
        dtype: torch.dtype,
    ) -> Optional[torch.Tensor]:
        """
        Zamienia listę / numpy-like input na Tensor.
        """

        if x is None:
            return None

        if isinstance(x, torch.Tensor):
            return x.to(
                device=device,
                dtype=dtype,
            )

        return torch.as_tensor(
            x,
            device=device,
            dtype=dtype,
        )

    def _prepare_feature(
        self,
        x: Optional[torch.Tensor],
        expected_dim: int,
        batch_size: int,
        device: torch.device,
        dtype: torch.dtype,
    ) -> torch.Tensor:
        """
        Przygotowanie pojedynczej modalności.

        Jeśli modalność nie została dostarczona, zwracany jest zerowy
        embedding.

        Dzięki temu model może działać także wtedy, gdy np. nie mamy
        danych RNA dla konkretnego przypadku.
        """

        if x is None:
            return torch.zeros(
                batch_size,
                expected_dim,
                device=device,
                dtype=dtype,
            )

        if x.ndim == 1:
            x = x.unsqueeze(0)

        if x.ndim != 2:
            raise ValueError(
                f"Expected 2D tensor [B, D], got shape={tuple(x.shape)}"
            )

        if x.shape[0] != batch_size:
            raise ValueError(
                "Batch size mismatch: "
                f"expected {batch_size}, got {x.shape[0]}"
            )

        if x.shape[1] != expected_dim:
            raise ValueError(
                f"Feature dimension mismatch: "
                f"expected {expected_dim}, got {x.shape[1]}"
            )

        return x.to(
            device=device,
            dtype=dtype,
        )

    # ======================================================================
    # Forward
    # ======================================================================

    def forward(
        self,
        image_features: Optional[torch.Tensor] = None,
        cell_features: Optional[torch.Tensor] = None,
        rna_features: Optional[torch.Tensor] = None,
        morphology_features: Optional[torch.Tensor] = None,
        hand_features: Optional[torch.Tensor] = None,
    ) -> AgingPrediction:
        """
        Forward pass.

        Wszystkie inputy mają postać:

            [batch_size, feature_dim]

        Przykład:

            image_features:
                [B, 768]

            cell_features:
                [B, 256]

            rna_features:
                [B, 256]

            morphology_features:
                [B, 128]

            hand_features:
                [B, 128]

        Modalności mogą być None.
        """

        # --------------------------------------------------------------
        # Determine device / dtype
        # --------------------------------------------------------------

        first_tensor = next(
            (
                x
                for x in [
                    image_features,
                    cell_features,
                    rna_features,
                    morphology_features,
                    hand_features,
                ]
                if isinstance(x, torch.Tensor)
            ),
            None,
        )

        if first_tensor is None:
            raise ValueError(
                "At least one input modality must be provided."
            )

        device = first_tensor.device
        dtype = first_tensor.dtype

        if first_tensor.ndim == 1:
            batch_size = 1
        else:
            batch_size = first_tensor.shape[0]

        # --------------------------------------------------------------
        # Prepare inputs
        # --------------------------------------------------------------

        image_features = self._prepare_feature(
            image_features,
            self.config.image_dim,
            batch_size,
            device,
            dtype,
        )

        cell_features = self._prepare_feature(
            cell_features,
            self.config.cell_dim,
            batch_size,
            device,
            dtype,
        )

        rna_features = self._prepare_feature(
            rna_features,
            self.config.rna_dim,
            batch_size,
            device,
            dtype,
        )

        morphology_features = self._prepare_feature(
            morphology_features,
            self.config.morphology_dim,
            batch_size,
            device,
            dtype,
        )

        hand_features = self._prepare_feature(
            hand_features,
            self.config.hand_dim,
            batch_size,
            device,
            dtype,
        )

        # --------------------------------------------------------------
        # Encode modalities
        # --------------------------------------------------------------

        image_embedding = self.image_encoder(
            image_features
        )

        cell_embedding = self.cell_encoder(
            cell_features
        )

        rna_embedding = self.rna_encoder(
            rna_features
        )

        morphology_embedding = self.morphology_encoder(
            morphology_features
        )

        hand_embedding = self.hand_encoder(
            hand_features
        )

        # --------------------------------------------------------------
        # Multimodal fusion
        # --------------------------------------------------------------

        fused_input = torch.cat(
            [
                image_embedding,
                cell_embedding,
                rna_embedding,
                morphology_embedding,
                hand_embedding,
            ],
            dim=-1,
        )

        fused_features = self.fusion(
            fused_input
        )

        # --------------------------------------------------------------
        # Aging representation
        # --------------------------------------------------------------

        aging_embedding = self.aging_representation(
            fused_features
        )

        # --------------------------------------------------------------
        # Age
        # --------------------------------------------------------------

        raw_age = self.age_head(
            aging_embedding
        ).squeeze(-1)

        predicted_age = torch.clamp(
            raw_age,
            min=self.config.min_age,
            max=self.config.max_age,
        )

        # --------------------------------------------------------------
        # Aging score
        # --------------------------------------------------------------

        aging_score = self.aging_score_head(
            aging_embedding
        ).squeeze(-1)

        # --------------------------------------------------------------
        # Uncertainty
        # --------------------------------------------------------------

        age_uncertainty = self.uncertainty_head(
            aging_embedding
        ).squeeze(-1)

        # --------------------------------------------------------------
        # Confidence
        #
        # Simple normalized confidence:
        #
        # confidence = 1 / (1 + uncertainty)
        # --------------------------------------------------------------

        confidence = 1.0 / (
            1.0 + age_uncertainty
        )

        confidence = torch.clamp(
            confidence,
            min=0.0,
            max=1.0,
        )

        return AgingPrediction(
            predicted_age=predicted_age,
            aging_score=aging_score,
            aging_embedding=aging_embedding,
            confidence=confidence,
            age_uncertainty=age_uncertainty,
            fused_features=fused_features,
        )

    # ======================================================================
    # Convenience methods
    # ======================================================================

    @torch.no_grad()
    def predict(
        self,
        image_features: Optional[torch.Tensor] = None,
        cell_features: Optional[torch.Tensor] = None,
        rna_features: Optional[torch.Tensor] = None,
        morphology_features: Optional[torch.Tensor] = None,
        hand_features: Optional[torch.Tensor] = None,
    ) -> AgingPrediction:
        """
        Tryb inference.
        """

        was_training = self.training

        self.eval()

        prediction = self.forward(
            image_features=image_features,
            cell_features=cell_features,
            rna_features=rna_features,
            morphology_features=morphology_features,
            hand_features=hand_features,
        )

        if was_training:
            self.train()

        return prediction

    @torch.no_grad()
    def extract_embedding(
        self,
        image_features: Optional[torch.Tensor] = None,
        cell_features: Optional[torch.Tensor] = None,
        rna_features: Optional[torch.Tensor] = None,
        morphology_features: Optional[torch.Tensor] = None,
        hand_features: Optional[torch.Tensor] = None,
    ) -> torch.Tensor:
        """
        Zwraca tylko embedding starzenia.
        """

        prediction = self.predict(
            image_features=image_features,
            cell_features=cell_features,
            rna_features=rna_features,
            morphology_features=morphology_features,
            hand_features=hand_features,
        )

        return prediction.aging_embedding


# ============================================================================
# Loss functions
# ============================================================================


class AgingLoss(nn.Module):
    """
    Funkcja straty dla modelu aging.

    Łączy:

        1. age regression loss
        2. aging score loss
        3. embedding regularization

    age_loss:
        SmoothL1Loss

    score_loss:
        Binary Cross Entropy

    embedding_loss:
        L2 regularization embeddingu.

    Parametry wag pozwalają później dostosować trening.
    """

    def __init__(
        self,
        age_weight: float = 1.0,
        score_weight: float = 0.25,
        embedding_weight: float = 1e-4,
    ) -> None:
        super().__init__()

        self.age_weight = age_weight
        self.score_weight = score_weight
        self.embedding_weight = embedding_weight

        self.age_loss = nn.SmoothL1Loss()

        self.score_loss = nn.BCELoss()

    def forward(
        self,
        prediction: AgingPrediction,
        target_age: torch.Tensor,
        target_aging_score: Optional[torch.Tensor] = None,
    ) -> Dict[str, torch.Tensor]:
        """
        Oblicza poszczególne składniki loss.

        target_age:
            [B]

        target_aging_score:
            [B], wartości 0-1.
        """

        if target_age.ndim > 1:
            target_age = target_age.squeeze(-1)

        target_age = target_age.to(
            device=prediction.predicted_age.device,
            dtype=prediction.predicted_age.dtype,
        )

        age_loss = self.age_loss(
            prediction.predicted_age,
            target_age,
        )

        total_loss = (
            self.age_weight * age_loss
        )

        losses = {
            "age_loss": age_loss,
        }

        if target_aging_score is not None:

            if target_aging_score.ndim > 1:
                target_aging_score = (
                    target_aging_score.squeeze(-1)
                )

            target_aging_score = target_aging_score.to(
                device=prediction.aging_score.device,
                dtype=prediction.aging_score.dtype,
            )

            score_loss = self.score_loss(
                prediction.aging_score,
                target_aging_score,
            )

            total_loss = (
                total_loss
                + self.score_weight * score_loss
            )

            losses["score_loss"] = score_loss

        # --------------------------------------------------------------
        # Embedding regularization
        # --------------------------------------------------------------

        embedding_loss = (
            prediction.aging_embedding
            .pow(2)
            .mean()
        )

        total_loss = (
            total_loss
            + self.embedding_weight * embedding_loss
        )

        losses["embedding_loss"] = embedding_loss
        losses["total_loss"] = total_loss

        return losses


# ============================================================================
# Model factory
# ============================================================================


def build_aging_model(
    config: Optional[AgingModelConfig] = None,
    device: Optional[Union[str, torch.device]] = None,
) -> AgingModel:
    """
    Tworzy AgingModel.

    Przykład:

        model = build_aging_model(
            device="cuda"
        )
    """

    model = AgingModel(
        config=config,
    )

    if device is not None:
        model = model.to(device)

    return model


# ============================================================================
# Checkpoint utilities
# ============================================================================


def save_aging_checkpoint(
    model: AgingModel,
    path: Union[str, Path],
    optimizer: Optional[torch.optim.Optimizer] = None,
    epoch: Optional[int] = None,
    loss: Optional[float] = None,
) -> None:
    """
    Zapisuje checkpoint modelu.
    """

    path = Path(path)

    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    checkpoint = {
        "model_state_dict": model.state_dict(),
        "config": model.config.__dict__,
    }

    if optimizer is not None:
        checkpoint[
            "optimizer_state_dict"
        ] = optimizer.state_dict()

    if epoch is not None:
        checkpoint["epoch"] = epoch

    if loss is not None:
        checkpoint["loss"] = loss

    torch.save(
        checkpoint,
        path,
    )


def load_aging_checkpoint(
    path: Union[str, Path],
    device: Optional[Union[str, torch.device]] = None,
    strict: bool = True,
) -> Tuple[AgingModel, Dict]:
    """
    Ładuje checkpoint AgingModel.

    Zwraca:

        model, checkpoint
    """

    path = Path(path)

    if not path.exists():
        raise FileNotFoundError(
            f"Checkpoint not found: {path}"
        )

    if device is None:
        device = "cpu"

    checkpoint = torch.load(
        path,
        map_location=device,
    )

    config_dict = checkpoint.get(
        "config",
        {},
    )

    config = AgingModelConfig(
        **config_dict
    )

    model = AgingModel(
        config=config,
    )

    model.load_state_dict(
        checkpoint["model_state_dict"],
        strict=strict,
    )

    model.to(device)

    return model, checkpoint


# ============================================================================
# Training helper
# ============================================================================


def train_aging_step(
    model: AgingModel,
    optimizer: torch.optim.Optimizer,
    loss_fn: AgingLoss,
    batch: Mapping[str, torch.Tensor],
) -> Dict[str, float]:
    """
    Wykonuje jeden krok treningowy.

    Oczekiwany batch:

        {
            "image_features": ...,
            "cell_features": ...,
            "rna_features": ...,
            "morphology_features": ...,
            "hand_features": ...,
            "target_age": ...,
            "target_aging_score": ...
        }

    Modalności są opcjonalne.
    """

    model.train()

    optimizer.zero_grad(
        set_to_none=True
    )

    prediction = model(
        image_features=batch.get(
            "image_features"
        ),
        cell_features=batch.get(
            "cell_features"
        ),
        rna_features=batch.get(
            "rna_features"
        ),
        morphology_features=batch.get(
            "morphology_features"
        ),
        hand_features=batch.get(
            "hand_features"
        ),
    )

    losses = loss_fn(
        prediction=prediction,
        target_age=batch["target_age"],
        target_aging_score=batch.get(
            "target_aging_score"
        ),
    )

    total_loss = losses[
        "total_loss"
    ]

    total_loss.backward()

    optimizer.step()

    return {
        key: float(value.detach().cpu())
        for key, value in losses.items()
    }


# ============================================================================
# Example
# ============================================================================


if __name__ == "__main__":

    # --------------------------------------------------------------
    # Configuration
    # --------------------------------------------------------------

    config = AgingModelConfig(
        image_dim=768,
        cell_dim=256,
        rna_dim=256,
        morphology_dim=128,
        hand_dim=128,
        hidden_dim=512,
        aging_embedding_dim=256,
    )

    # --------------------------------------------------------------
    # Model
    # --------------------------------------------------------------

    device = torch.device(
        "cuda"
        if torch.cuda.is_available()
        else "cpu"
    )

    model = AgingModel(
        config=config
    ).to(device)

    # --------------------------------------------------------------
    # Example batch
    # --------------------------------------------------------------

    batch_size = 4

    image_features = torch.randn(
        batch_size,
        config.image_dim,
        device=device,
    )

    cell_features = torch.randn(
        batch_size,
        config.cell_dim,
        device=device,
    )

    rna_features = torch.randn(
        batch_size,
        config.rna_dim,
        device=device,
    )

    morphology_features = torch.randn(
        batch_size,
        config.morphology_dim,
        device=device,
    )

    hand_features = torch.randn(
        batch_size,
        config.hand_dim,
        device=device,
    )

    target_age = torch.tensor(
        [25.0, 35.0, 50.0, 70.0],
        device=device,
    )

    target_aging_score = torch.tensor(
        [0.15, 0.35, 0.60, 0.85],
        device=device,
    )

    # --------------------------------------------------------------
    # Forward
    # --------------------------------------------------------------

    prediction = model(
        image_features=image_features,
        cell_features=cell_features,
        rna_features=rna_features,
        morphology_features=morphology_features,
        hand_features=hand_features,
    )

    print(
        "Predicted age:",
        prediction.predicted_age,
    )

    print(
        "Aging score:",
        prediction.aging_score,
    )

    print(
        "Confidence:",
        prediction.confidence,
    )

    print(
        "Embedding shape:",
        prediction.aging_embedding.shape,
    )

    # --------------------------------------------------------------
    # Loss
    # --------------------------------------------------------------

    loss_fn = AgingLoss()

    losses = loss_fn(
        prediction=prediction,
        target_age=target_age,
        target_aging_score=target_aging_score,
    )

    print(
        "Loss:",
        losses["total_loss"].item(),
    )

    # --------------------------------------------------------------
    # Optimizer
    # --------------------------------------------------------------

    optimizer = torch.optim.AdamW(
        model.parameters(),
        lr=1e-4,
        weight_decay=1e-4,
    )

    # --------------------------------------------------------------
    # One training step
    # --------------------------------------------------------------

    batch = {
        "image_features": image_features,
        "cell_features": cell_features,
        "rna_features": rna_features,
        "morphology_features": morphology_features,
        "hand_features": hand_features,
        "target_age": target_age,
        "target_aging_score": target_aging_score,
    }

    metrics = train_aging_step(
        model=model,
        optimizer=optimizer,
        loss_fn=loss_fn,
        batch=batch,
    )

    print(
        "Training metrics:",
        metrics,
    )