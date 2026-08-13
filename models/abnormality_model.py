"""
models/abnormality_model.py

Model wykrywania nieprawidłowości biologicznych / morfologicznych.

Odpowiedzialność modułu:
    - przyjmowanie cech/embeddingów z różnych modalności,
    - klasyfikacja normal / abnormal,
    - opcjonalna klasyfikacja wieloklasowa typu abnormality,
    - generowanie score anomalii,
    - obsługa brakujących modalności,
    - możliwość wykorzystania gotowego embeddingu multimodalnego,
    - zwracanie ustandaryzowanego wyniku predykcji.

Moduł NIE odpowiada za:
    - preprocessing obrazów,
    - segmentację komórek,
    - ekstrakcję embeddingów,
    - analizę RNA,
    - decyzję kliniczną,
    - rekomendację interwencji.

Te zadania są realizowane przez odpowiednie moduły pipeline/analysis/decision.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Sequence, Tuple, Union

import torch
import torch.nn as nn
import torch.nn.functional as F


TensorLike = Union[torch.Tensor, Sequence[float]]


# ============================================================================
# Configuration
# ============================================================================

@dataclass
class AbnormalityModelConfig:
    """
    Konfiguracja modelu abnormality detection.

    Można ją później przenieść do configs/models.yaml.
    """

    input_dim: int = 768
    hidden_dim: int = 512

    num_classes: int = 2

    dropout: float = 0.2

    num_layers: int = 2

    use_batch_norm: bool = True
    use_layer_norm: bool = False

    # Jeśli True, model zwraca również score abnormality.
    return_abnormality_score: bool = True

    # Nazwy klas dla klasyfikacji wieloklasowej.
    class_names: Tuple[str, ...] = (
        "normal",
        "abnormal",
    )

    # Próg dla klasyfikacji binarnej.
    abnormal_threshold: float = 0.5

    # Urządzenie.
    device: str = "cuda" if torch.cuda.is_available() else "cpu"


# ============================================================================
# Prediction output
# ============================================================================

@dataclass
class AbnormalityPrediction:
    """
    Ustandaryzowany wynik predykcji.

    Dzięki temu pozostałe moduły projektu nie muszą znać
    szczegółów implementacji sieci.
    """

    predicted_class: int

    predicted_label: str

    abnormality_score: float

    probabilities: List[float]

    class_names: List[str]

    logits: Optional[List[float]] = None

    metadata: Dict[str, Union[str, float, int, bool]] = field(
        default_factory=dict
    )

    def is_abnormal(self) -> bool:
        """
        Zwraca True, jeśli przewidziana klasa jest różna od normal.
        """

        return self.predicted_label != "normal"


# ============================================================================
# Building blocks
# ============================================================================

class MLPBlock(nn.Module):
    """
    Podstawowy blok MLP używany w encoderze abnormality model.
    """

    def __init__(
        self,
        input_dim: int,
        output_dim: int,
        dropout: float = 0.2,
        use_batch_norm: bool = True,
        use_layer_norm: bool = False,
    ) -> None:
        super().__init__()

        layers: List[nn.Module] = [
            nn.Linear(input_dim, output_dim)
        ]

        if use_batch_norm:
            layers.append(nn.BatchNorm1d(output_dim))

        if use_layer_norm:
            layers.append(nn.LayerNorm(output_dim))

        layers.extend(
            [
                nn.GELU(),
                nn.Dropout(dropout),
            ]
        )

        self.block = nn.Sequential(*layers)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.block(x)


# ============================================================================
# Main neural network
# ============================================================================

class AbnormalityNetwork(nn.Module):
    """
    Główna sieć neuronowa do klasyfikacji nieprawidłowości.

    Architektura:

        input embedding
             ↓
        MLP encoder
             ↓
        latent representation
             ↓
        classification head
             ↓
        logits

    Model jest celowo niezależny od konkretnego źródła embeddingu.
    """

    def __init__(
        self,
        input_dim: int,
        hidden_dim: int = 512,
        num_classes: int = 2,
        dropout: float = 0.2,
        num_layers: int = 2,
        use_batch_norm: bool = True,
        use_layer_norm: bool = False,
    ) -> None:

        super().__init__()

        if num_layers < 1:
            raise ValueError("num_layers must be >= 1")

        layers: List[nn.Module] = []

        current_dim = input_dim

        for _ in range(num_layers):
            layers.append(
                MLPBlock(
                    input_dim=current_dim,
                    output_dim=hidden_dim,
                    dropout=dropout,
                    use_batch_norm=use_batch_norm,
                    use_layer_norm=use_layer_norm,
                )
            )

            current_dim = hidden_dim

        self.encoder = nn.Sequential(*layers)

        self.classifier = nn.Sequential(
            nn.Linear(hidden_dim, hidden_dim // 2),
            nn.GELU(),
            nn.Dropout(dropout),
            nn.Linear(hidden_dim // 2, num_classes),
        )

        self.embedding_projection = nn.Identity()

    def encode(
        self,
        x: torch.Tensor,
    ) -> torch.Tensor:
        """
        Zwraca latent representation.
        """

        return self.encoder(x)

    def forward(
        self,
        x: torch.Tensor,
    ) -> torch.Tensor:
        """
        Forward pass.

        Returns:
            logits: [batch_size, num_classes]
        """

        latent = self.encode(x)

        logits = self.classifier(latent)

        return logits


# ============================================================================
# Abnormality Model
# ============================================================================

class AbnormalityModel(nn.Module):
    """
    Wysokopoziomowy interfejs abnormality detection.

    Obsługuje:

        - pojedynczy embedding,
        - batch embeddingów,
        - embedding multimodalny,
        - predykcję normal/abnormal,
        - klasyfikację wieloklasową,
        - abnormality score,
        - zapis i ładowanie checkpointów.
    """

    def __init__(
        self,
        config: Optional[AbnormalityModelConfig] = None,
    ) -> None:

        super().__init__()

        self.config = config or AbnormalityModelConfig()

        if self.config.num_classes < 2:
            raise ValueError(
                "num_classes must be >= 2"
            )

        if len(self.config.class_names) != self.config.num_classes:
            raise ValueError(
                "Length of class_names must match num_classes."
            )

        self.network = AbnormalityNetwork(
            input_dim=self.config.input_dim,
            hidden_dim=self.config.hidden_dim,
            num_classes=self.config.num_classes,
            dropout=self.config.dropout,
            num_layers=self.config.num_layers,
            use_batch_norm=self.config.use_batch_norm,
            use_layer_norm=self.config.use_layer_norm,
        )

        self.to(self.config.device)

    # ------------------------------------------------------------------------
    # Forward
    # ------------------------------------------------------------------------

    def forward(
        self,
        x: torch.Tensor,
    ) -> torch.Tensor:
        """
        Forward pass.

        Args:
            x:
                Tensor [batch, input_dim]

        Returns:
            logits:
                Tensor [batch, num_classes]
        """

        x = self._prepare_input(x)

        return self.network(x)

    # ------------------------------------------------------------------------
    # Input handling
    # ------------------------------------------------------------------------

    def _prepare_input(
        self,
        x: TensorLike,
    ) -> torch.Tensor:
        """
        Przygotowuje embedding do wejścia modelu.
        """

        if not isinstance(x, torch.Tensor):
            x = torch.tensor(
                x,
                dtype=torch.float32,
            )

        x = x.float()

        if x.ndim == 1:
            x = x.unsqueeze(0)

        if x.ndim != 2:
            raise ValueError(
                "Expected input shape [batch, embedding_dim]. "
                f"Received shape: {tuple(x.shape)}"
            )

        if x.shape[-1] != self.config.input_dim:
            raise ValueError(
                "Invalid embedding dimension. "
                f"Expected {self.config.input_dim}, "
                f"received {x.shape[-1]}."
            )

        return x.to(self.config.device)

    # ------------------------------------------------------------------------
    # Probability
    # ------------------------------------------------------------------------

    @staticmethod
    def logits_to_probabilities(
        logits: torch.Tensor,
    ) -> torch.Tensor:
        """
        Zamienia logits na prawdopodobieństwa.
        """

        return F.softmax(
            logits,
            dim=-1,
        )

    # ------------------------------------------------------------------------
    # Abnormality score
    # ------------------------------------------------------------------------

    def calculate_abnormality_score(
        self,
        probabilities: torch.Tensor,
    ) -> torch.Tensor:
        """
        Oblicza abnormality score.

        Dla klasyfikacji binarnej:

            P(abnormal)

        Dla klasyfikacji wieloklasowej:

            1 - P(normal)

        Zakładamy, że pierwsza klasa to "normal".
        """

        if probabilities.ndim != 2:
            raise ValueError(
                "Expected probabilities with shape [batch, classes]."
            )

        if probabilities.shape[1] < 2:
            raise ValueError(
                "At least two classes are required."
            )

        normal_probability = probabilities[:, 0]

        abnormality_score = 1.0 - normal_probability

        return abnormality_score

    # ------------------------------------------------------------------------
    # Prediction
    # ------------------------------------------------------------------------

    @torch.no_grad()
    def predict(
        self,
        x: TensorLike,
    ) -> List[AbnormalityPrediction]:
        """
        Wykonuje predykcję dla embeddingów.

        Args:
            x:
                [embedding_dim]
                lub
                [batch, embedding_dim]

        Returns:
            Lista AbnormalityPrediction.
        """

        self.eval()

        x_tensor = self._prepare_input(x)

        logits = self.network(x_tensor)

        probabilities = self.logits_to_probabilities(
            logits
        )

        predicted_classes = torch.argmax(
            probabilities,
            dim=-1,
        )

        abnormality_scores = self.calculate_abnormality_score(
            probabilities
        )

        predictions: List[AbnormalityPrediction] = []

        for i in range(x_tensor.shape[0]):

            class_index = int(
                predicted_classes[i].item()
            )

            probability_vector = (
                probabilities[i]
                .detach()
                .cpu()
                .tolist()
            )

            logits_vector = (
                logits[i]
                .detach()
                .cpu()
                .tolist()
            )

            abnormality_score = float(
                abnormality_scores[i].item()
            )

            label = self.config.class_names[
                class_index
            ]

            prediction = AbnormalityPrediction(
                predicted_class=class_index,
                predicted_label=label,
                abnormality_score=abnormality_score,
                probabilities=probability_vector,
                class_names=list(
                    self.config.class_names
                ),
                logits=logits_vector,
                metadata={
                    "threshold": self.config.abnormal_threshold,
                },
            )

            predictions.append(prediction)

        return predictions

    # ------------------------------------------------------------------------
    # Binary prediction
    # ------------------------------------------------------------------------

    @torch.no_grad()
    def predict_binary(
        self,
        x: TensorLike,
    ) -> List[AbnormalityPrediction]:
        """
        Predykcja normal / abnormal z wykorzystaniem threshold.

        Jest to przydatne, gdy chcemy oddzielić:

            model probability

        od:

            decyzji thresholdowej.
        """

        self.eval()

        x_tensor = self._prepare_input(x)

        logits = self.network(x_tensor)

        probabilities = self.logits_to_probabilities(
            logits
        )

        abnormality_scores = self.calculate_abnormality_score(
            probabilities
        )

        predictions: List[AbnormalityPrediction] = []

        for i in range(x_tensor.shape[0]):

            score = float(
                abnormality_scores[i].item()
            )

            if score >= self.config.abnormal_threshold:
                predicted_label = "abnormal"
                predicted_class = 1
            else:
                predicted_label = "normal"
                predicted_class = 0

            predictions.append(
                AbnormalityPrediction(
                    predicted_class=predicted_class,
                    predicted_label=predicted_label,
                    abnormality_score=score,
                    probabilities=(
                        probabilities[i]
                        .detach()
                        .cpu()
                        .tolist()
                    ),
                    class_names=list(
                        self.config.class_names
                    ),
                    logits=(
                        logits[i]
                        .detach()
                        .cpu()
                        .tolist()
                    ),
                    metadata={
                        "threshold": self.config.abnormal_threshold,
                        "thresholded": True,
                    },
                )
            )

        return predictions

    # ------------------------------------------------------------------------
    # Embedding extraction
    # ------------------------------------------------------------------------

    @torch.no_grad()
    def extract_embedding(
        self,
        x: TensorLike,
    ) -> torch.Tensor:
        """
        Zwraca latent embedding z encoder'a.

        Przydatne np. do:

            outputs/embeddings/

        lub dalszego fusion.
        """

        self.eval()

        x_tensor = self._prepare_input(x)

        embedding = self.network.encode(
            x_tensor
        )

        return embedding

    # ------------------------------------------------------------------------
    # Training loss
    # ------------------------------------------------------------------------

    def compute_loss(
        self,
        logits: torch.Tensor,
        targets: torch.Tensor,
        class_weights: Optional[torch.Tensor] = None,
    ) -> torch.Tensor:
        """
        Cross-entropy loss.

        Args:
            logits:
                [batch, num_classes]

            targets:
                [batch]

            class_weights:
                opcjonalne wagi klas.
        """

        targets = targets.long().to(
            logits.device
        )

        if class_weights is not None:
            class_weights = class_weights.to(
                logits.device
            )

        return F.cross_entropy(
            logits,
            targets,
            weight=class_weights,
        )

    # ------------------------------------------------------------------------
    # Multimodal input
    # ------------------------------------------------------------------------

    def combine_modalities(
        self,
        embeddings: Dict[str, torch.Tensor],
    ) -> torch.Tensor:
        """
        Łączy embeddingi z różnych modalności.

        Przykład:

            {
                "image": image_embedding,
                "cells": cell_embedding,
                "rna": rna_embedding,
                "hand": hand_embedding
            }

        Wszystkie embeddingi muszą mieć taki sam batch size.

        UWAGA:
        Jest to prosty mechanizm concatenation.
        Docelowo główna fuzja powinna być wykonywana przez
        fusion_model.py.
        """

        if not embeddings:
            raise ValueError(
                "No embeddings were provided."
            )

        tensors = []

        batch_size: Optional[int] = None

        for name, tensor in embeddings.items():

            if not isinstance(tensor, torch.Tensor):
                raise TypeError(
                    f"Embedding '{name}' must be a torch.Tensor."
                )

            if tensor.ndim == 1:
                tensor = tensor.unsqueeze(0)

            if tensor.ndim != 2:
                raise ValueError(
                    f"Embedding '{name}' must have shape "
                    "[batch, dim]."
                )

            if batch_size is None:
                batch_size = tensor.shape[0]

            elif tensor.shape[0] != batch_size:
                raise ValueError(
                    "All modality embeddings must have "
                    "the same batch size."
                )

            tensors.append(
                tensor.float()
            )

        return torch.cat(
            tensors,
            dim=-1,
        )

    # ------------------------------------------------------------------------
    # Device
    # ------------------------------------------------------------------------

    def set_device(
        self,
        device: Union[str, torch.device],
    ) -> None:
        """
        Przenosi model na wskazane urządzenie.
        """

        self.config.device = str(device)

        self.to(device)

    # ------------------------------------------------------------------------
    # Checkpoint
    # ------------------------------------------------------------------------

    def save_checkpoint(
        self,
        path: str,
        optimizer: Optional[torch.optim.Optimizer] = None,
        epoch: Optional[int] = None,
        metrics: Optional[Dict[str, float]] = None,
    ) -> None:
        """
        Zapisuje checkpoint modelu.
        """

        checkpoint = {
            "model_state_dict": self.state_dict(),
            "config": self.config.__dict__,
            "epoch": epoch,
            "metrics": metrics or {},
        }

        if optimizer is not None:
            checkpoint[
                "optimizer_state_dict"
            ] = optimizer.state_dict()

        torch.save(
            checkpoint,
            path,
        )

    # ------------------------------------------------------------------------

    def load_checkpoint(
        self,
        path: str,
        optimizer: Optional[torch.optim.Optimizer] = None,
        strict: bool = True,
        map_location: Optional[str] = None,
    ) -> Dict:
        """
        Ładuje checkpoint.

        Returns:
            metadata checkpointu.
        """

        if map_location is None:
            map_location = self.config.device

        checkpoint = torch.load(
            path,
            map_location=map_location,
        )

        if "model_state_dict" not in checkpoint:
            raise KeyError(
                "Checkpoint does not contain "
                "'model_state_dict'."
            )

        self.load_state_dict(
            checkpoint["model_state_dict"],
            strict=strict,
        )

        if (
            optimizer is not None
            and "optimizer_state_dict" in checkpoint
        ):
            optimizer.load_state_dict(
                checkpoint[
                    "optimizer_state_dict"
                ]
            )

        return checkpoint

    # ------------------------------------------------------------------------
    # Model summary
    # ------------------------------------------------------------------------

    def get_model_info(self) -> Dict[str, Union[int, float, str]]:
        """
        Zwraca podstawowe informacje o modelu.
        """

        num_parameters = sum(
            p.numel()
            for p in self.parameters()
        )

        trainable_parameters = sum(
            p.numel()
            for p in self.parameters()
            if p.requires_grad
        )

        return {
            "input_dim": self.config.input_dim,
            "hidden_dim": self.config.hidden_dim,
            "num_classes": self.config.num_classes,
            "dropout": self.config.dropout,
            "parameters": num_parameters,
            "trainable_parameters": trainable_parameters,
            "device": str(
                self.config.device
            ),
        }


# ============================================================================
# Factory
# ============================================================================

def build_abnormality_model(
    input_dim: int = 768,
    num_classes: int = 2,
    class_names: Optional[Tuple[str, ...]] = None,
    device: Optional[str] = None,
) -> AbnormalityModel:
    """
    Fabryka modelu.

    Przykład:

        model = build_abnormality_model(
            input_dim=768,
            num_classes=2,
            class_names=("normal", "abnormal"),
        )
    """

    if class_names is None:

        if num_classes == 2:
            class_names = (
                "normal",
                "abnormal",
            )

        else:
            class_names = tuple(
                f"class_{i}"
                for i in range(num_classes)
            )

    if device is None:
        device = (
            "cuda"
            if torch.cuda.is_available()
            else "cpu"
        )

    config = AbnormalityModelConfig(
        input_dim=input_dim,
        num_classes=num_classes,
        class_names=class_names,
        device=device,
    )

    return AbnormalityModel(
        config=config
    )


# ============================================================================
# Utility functions
# ============================================================================

def load_abnormality_model(
    checkpoint_path: str,
    device: Optional[str] = None,
) -> AbnormalityModel:
    """
    Ładuje model z checkpointu.

    UWAGA:
    Konfiguracja jest pobierana z checkpointu.
    """

    map_location = (
        device
        if device is not None
        else (
            "cuda"
            if torch.cuda.is_available()
            else "cpu"
        )
    )

    checkpoint = torch.load(
        checkpoint_path,
        map_location=map_location,
    )

    checkpoint_config = checkpoint.get(
        "config",
        {},
    )

    config = AbnormalityModelConfig(
        **checkpoint_config
    )

    if device is not None:
        config.device = device

    model = AbnormalityModel(
        config=config
    )

    model.load_state_dict(
        checkpoint[
            "model_state_dict"
        ]
    )

    model.eval()

    return model


# ============================================================================
# Example
# ============================================================================

if __name__ == "__main__":

    print("=" * 70)
    print("Abnormality Model")
    print("=" * 70)

    # ------------------------------------------------------------
    # Create model
    # ------------------------------------------------------------

    model = build_abnormality_model(
        input_dim=768,
        num_classes=2,
        class_names=(
            "normal",
            "abnormal",
        ),
    )

    # ------------------------------------------------------------
    # Model information
    # ------------------------------------------------------------

    info = model.get_model_info()

    for key, value in info.items():
        print(
            f"{key}: {value}"
        )

    # ------------------------------------------------------------
    # Dummy embedding
    # ------------------------------------------------------------

    embedding = torch.randn(
        1,
        768,
    )

    # ------------------------------------------------------------
    # Prediction
    # ------------------------------------------------------------

    predictions = model.predict(
        embedding
    )

    prediction = predictions[0]

    print()
    print("Prediction:")
    print(
        f"  class: {prediction.predicted_label}"
    )
    print(
        f"  abnormality score: "
        f"{prediction.abnormality_score:.4f}"
    )
    print(
        f"  probabilities: "
        f"{prediction.probabilities}"
    )

    # ------------------------------------------------------------
    # Binary prediction
    # ------------------------------------------------------------

    binary_prediction = model.predict_binary(
        embedding
    )[0]

    print()
    print("Binary prediction:")
    print(
        f"  label: "
        f"{binary_prediction.predicted_label}"
    )
    print(
        f"  score: "
        f"{binary_prediction.abnormality_score:.4f}"
    )

    # ------------------------------------------------------------
    # Extract latent embedding
    # ------------------------------------------------------------

    latent = model.extract_embedding(
        embedding
    )

    print()
    print(
        f"Latent embedding shape: "
        f"{tuple(latent.shape)}"
    )

    print()
    print("Model ready.")