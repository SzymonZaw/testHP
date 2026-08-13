"""
pathology_model.py

Moduł odpowiedzialny za analizę patologicznych zmian skóry.

Główne zadania:
- klasyfikacja patologii,
- ocena prawdopodobieństwa zmian,
- agregacja predykcji z wielu patchy WSI,
- analiza wyników histopatologicznych,
- przygotowanie cech dla fusion_model.py,
- obsługa klas:
    normal
    BCC
    melanoma
    other_lesion

Moduł NIE wykonuje:
- bezpośredniego odczytu WSI,
- segmentacji komórek,
- preprocessingu obrazu,
- ekstrakcji embeddingów DINOv2.

Te zadania realizują odpowiednio:
- monai_pipeline.py
- cellpose_model.py
- dinov2_model.py
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Sequence, Tuple, Union

import numpy as np

try:
    import torch
    import torch.nn as nn
    import torch.nn.functional as F
except ImportError:  # pragma: no cover
    torch = None
    nn = None
    F = None


# ============================================================================
# CONFIGURATION
# ============================================================================

DEFAULT_CLASSES = (
    "normal",
    "bcc",
    "melanoma",
    "other_lesion",
)


# ============================================================================
# DATA STRUCTURES
# ============================================================================

@dataclass
class PathologyPrediction:
    """
    Wynik klasyfikacji patologicznej.

    Attributes
    ----------
    label:
        Klasa z najwyższym prawdopodobieństwem.

    probabilities:
        Słownik:
            class_name -> probability

    confidence:
        Najwyższe prawdopodobieństwo.

    abnormal:
        Czy przypadek został uznany za nieprawidłowy.

    risk_score:
        Uproszczony score patologiczny w zakresie 0-1.
    """

    label: str
    probabilities: Dict[str, float]
    confidence: float
    abnormal: bool
    risk_score: float

    metadata: Dict[str, Union[str, float, int, bool]] = field(
        default_factory=dict
    )

    def to_dict(self) -> Dict:
        return {
            "label": self.label,
            "probabilities": self.probabilities,
            "confidence": self.confidence,
            "abnormal": self.abnormal,
            "risk_score": self.risk_score,
            "metadata": self.metadata,
        }


@dataclass
class PatchPrediction:
    """
    Predykcja pojedynczego patcha WSI.
    """

    patch_id: str
    probabilities: Dict[str, float]
    x: Optional[int] = None
    y: Optional[int] = None
    level: Optional[int] = None

    @property
    def label(self) -> str:
        return max(
            self.probabilities,
            key=self.probabilities.get,
        )

    @property
    def confidence(self) -> float:
        return float(max(self.probabilities.values()))


@dataclass
class PathologyConfig:
    """
    Konfiguracja modelu patologicznego.
    """

    classes: Tuple[str, ...] = DEFAULT_CLASSES

    abnormal_threshold: float = 0.50

    # Próg, od którego przypadek jest traktowany
    # jako wymagający zwiększonej uwagi.
    high_risk_threshold: float = 0.70

    # Minimalna pewność klasyfikacji.
    confidence_threshold: float = 0.50

    # Waga melanoma w końcowym risk score.
    melanoma_weight: float = 1.00

    # Waga BCC.
    bcc_weight: float = 0.75

    # Waga innych zmian.
    other_lesion_weight: float = 0.35


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def _softmax_numpy(
    logits: np.ndarray,
    axis: int = -1,
) -> np.ndarray:
    """
    Stabilna numerycznie funkcja softmax.
    """

    logits = np.asarray(logits, dtype=np.float32)

    shifted = logits - np.max(
        logits,
        axis=axis,
        keepdims=True,
    )

    exp_values = np.exp(shifted)

    return exp_values / np.sum(
        exp_values,
        axis=axis,
        keepdims=True,
    )


def _normalize_probabilities(
    probabilities: Dict[str, float],
    classes: Sequence[str],
) -> Dict[str, float]:
    """
    Uzupełnia brakujące klasy zerami i normalizuje rozkład.
    """

    values = np.array(
        [
            float(probabilities.get(class_name, 0.0))
            for class_name in classes
        ],
        dtype=np.float32,
    )

    total = float(values.sum())

    if total <= 0.0:
        values[:] = 1.0 / len(classes)
    else:
        values /= total

    return {
        class_name: float(value)
        for class_name, value in zip(classes, values)
    }


# ============================================================================
# PYTORCH MODEL
# ============================================================================

if torch is not None:

    class PathologyClassifier(nn.Module):
        """
        Prosty klasyfikator patologiczny.

        Model przyjmuje embedding obrazu, np.:
            DINOv2 embedding
            CNN embedding
            MONAI feature vector

        i zwraca logits dla klas patologicznych.

        Przykład:
            embedding_dim = 768
            num_classes = 4
        """

        def __init__(
            self,
            embedding_dim: int = 768,
            num_classes: int = len(DEFAULT_CLASSES),
            hidden_dim: int = 256,
            dropout: float = 0.2,
        ) -> None:

            super().__init__()

            self.embedding_dim = embedding_dim
            self.num_classes = num_classes

            self.classifier = nn.Sequential(
                nn.Linear(
                    embedding_dim,
                    hidden_dim,
                ),
                nn.LayerNorm(hidden_dim),
                nn.GELU(),
                nn.Dropout(dropout),

                nn.Linear(
                    hidden_dim,
                    hidden_dim // 2,
                ),
                nn.GELU(),
                nn.Dropout(dropout),

                nn.Linear(
                    hidden_dim // 2,
                    num_classes,
                ),
            )

        def forward(
            self,
            x: torch.Tensor,
        ) -> torch.Tensor:

            if x.ndim == 1:
                x = x.unsqueeze(0)

            return self.classifier(x)


# ============================================================================
# PATHOLOGY MODEL
# ============================================================================

class PathologyModel:
    """
    Główna klasa odpowiedzialna za analizę patologii.

    Architektura logiczna:

        WSI
         |
         v
    MONAI / preprocessing
         |
         v
       patches
         |
         v
      DINOv2
         |
         v
      embeddings
         |
         v
    PathologyModel
         |
         +---- normal
         +---- BCC
         +---- melanoma
         +---- other lesion
         |
         v
      pathology score
    """

    def __init__(
        self,
        embedding_dim: int = 768,
        config: Optional[PathologyConfig] = None,
        device: Optional[str] = None,
    ) -> None:

        self.config = config or PathologyConfig()

        self.embedding_dim = embedding_dim

        if torch is not None:

            if device is None:
                device = (
                    "cuda"
                    if torch.cuda.is_available()
                    else "cpu"
                )

            self.device = torch.device(device)

            self.model = PathologyClassifier(
                embedding_dim=embedding_dim,
                num_classes=len(self.config.classes),
            ).to(self.device)

        else:

            self.device = None
            self.model = None

    # ---------------------------------------------------------------------
    # MODEL MANAGEMENT
    # ---------------------------------------------------------------------

    def load_checkpoint(
        self,
        checkpoint_path: str,
        strict: bool = True,
    ) -> None:
        """
        Ładuje checkpoint modelu.

        Parameters
        ----------
        checkpoint_path:
            Ścieżka do checkpointu.

        strict:
            Czy wymagać dokładnego dopasowania parametrów.
        """

        if torch is None:
            raise ImportError(
                "PyTorch jest wymagany do ładowania checkpointu."
            )

        checkpoint = torch.load(
            checkpoint_path,
            map_location=self.device,
        )

        if isinstance(checkpoint, dict):

            if "state_dict" in checkpoint:
                state_dict = checkpoint["state_dict"]

            elif "model_state_dict" in checkpoint:
                state_dict = checkpoint["model_state_dict"]

            else:
                state_dict = checkpoint

        else:
            state_dict = checkpoint

        self.model.load_state_dict(
            state_dict,
            strict=strict,
        )

        self.model.eval()

    def save_checkpoint(
        self,
        checkpoint_path: str,
    ) -> None:
        """
        Zapisuje checkpoint modelu.
        """

        if torch is None:
            raise ImportError(
                "PyTorch jest wymagany do zapisu checkpointu."
            )

        torch.save(
            {
                "model_state_dict": self.model.state_dict(),
                "embedding_dim": self.embedding_dim,
                "classes": self.config.classes,
            },
            checkpoint_path,
        )

    def eval(self) -> None:
        """
        Przełącza model w tryb ewaluacji.
        """

        if self.model is not None:
            self.model.eval()

    def train(self) -> None:
        """
        Przełącza model w tryb treningowy.
        """

        if self.model is not None:
            self.model.train()

    # ---------------------------------------------------------------------
    # SINGLE EMBEDDING
    # ---------------------------------------------------------------------

    def predict_embedding(
        self,
        embedding: Union[
            np.ndarray,
            "torch.Tensor",
        ],
    ) -> PathologyPrediction:
        """
        Klasyfikuje pojedynczy embedding.

        Parameters
        ----------
        embedding:
            Wektor cech, np. embedding DINOv2.

        Returns
        -------
        PathologyPrediction
        """

        if torch is None:
            raise ImportError(
                "PyTorch jest wymagany do predykcji."
            )

        if isinstance(embedding, np.ndarray):

            tensor = torch.from_numpy(
                embedding.astype(np.float32)
            )

        else:

            tensor = embedding.float()

        if tensor.ndim == 1:
            tensor = tensor.unsqueeze(0)

        tensor = tensor.to(self.device)

        self.model.eval()

        with torch.no_grad():

            logits = self.model(tensor)

            probabilities = F.softmax(
                logits,
                dim=-1,
            )

        probabilities_np = (
            probabilities[0]
            .detach()
            .cpu()
            .numpy()
        )

        probability_dict = {
            class_name: float(probability)
            for class_name, probability in zip(
                self.config.classes,
                probabilities_np,
            )
        }

        return self._build_prediction(
            probability_dict
        )

    # ---------------------------------------------------------------------
    # LOGITS
    # ---------------------------------------------------------------------

    def predict_logits(
        self,
        embedding: Union[
            np.ndarray,
            "torch.Tensor",
        ],
    ) -> np.ndarray:
        """
        Zwraca surowe logits modelu.
        """

        if torch is None:
            raise ImportError(
                "PyTorch jest wymagany do predykcji."
            )

        if isinstance(embedding, np.ndarray):

            tensor = torch.from_numpy(
                embedding.astype(np.float32)
            )

        else:

            tensor = embedding.float()

        if tensor.ndim == 1:
            tensor = tensor.unsqueeze(0)

        tensor = tensor.to(self.device)

        self.model.eval()

        with torch.no_grad():

            logits = self.model(tensor)

        return (
            logits
            .detach()
            .cpu()
            .numpy()
        )

    # ---------------------------------------------------------------------
    # BATCH PREDICTION
    # ---------------------------------------------------------------------

    def predict_batch(
        self,
        embeddings: Union[
            np.ndarray,
            "torch.Tensor",
        ],
        batch_size: int = 32,
    ) -> List[PathologyPrediction]:
        """
        Klasyfikuje wiele embeddingów.

        Parameters
        ----------
        embeddings:
            Macierz:
                [N, embedding_dim]

        batch_size:
            Rozmiar batcha.
        """

        if torch is None:
            raise ImportError(
                "PyTorch jest wymagany do predykcji."
            )

        if isinstance(embeddings, np.ndarray):

            tensor = torch.from_numpy(
                embeddings.astype(np.float32)
            )

        else:

            tensor = embeddings.float()

        if tensor.ndim == 1:
            tensor = tensor.unsqueeze(0)

        tensor = tensor.to(self.device)

        self.model.eval()

        predictions: List[PathologyPrediction] = []

        with torch.no_grad():

            for start in range(
                0,
                len(tensor),
                batch_size,
            ):

                batch = tensor[
                    start:start + batch_size
                ]

                logits = self.model(batch)

                probs = F.softmax(
                    logits,
                    dim=-1,
                )

                probs_np = (
                    probs
                    .detach()
                    .cpu()
                    .numpy()
                )

                for row in probs_np:

                    probability_dict = {
                        class_name: float(probability)
                        for class_name, probability in zip(
                            self.config.classes,
                            row,
                        )
                    }

                    predictions.append(
                        self._build_prediction(
                            probability_dict
                        )
                    )

        return predictions

    # ---------------------------------------------------------------------
    # PATCH AGGREGATION
    # ---------------------------------------------------------------------

    def aggregate_patch_predictions(
        self,
        patch_predictions: Sequence[
            PatchPrediction
        ],
    ) -> PathologyPrediction:
        """
        Agreguje predykcje wielu patchy WSI.

        Domyślnie używane jest średnie prawdopodobieństwo
        dla każdej klasy.

        Przykład:

            patch 1:
                melanoma = 0.8

            patch 2:
                melanoma = 0.7

            patch 3:
                melanoma = 0.9

        wynik:

            melanoma = 0.8
        """

        if len(patch_predictions) == 0:

            raise ValueError(
                "Brak predykcji patchy do agregacji."
            )

        probability_matrix = []

        for prediction in patch_predictions:

            normalized = _normalize_probabilities(
                prediction.probabilities,
                self.config.classes,
            )

            probability_matrix.append(
                [
                    normalized[class_name]
                    for class_name in self.config.classes
                ]
            )

        matrix = np.asarray(
            probability_matrix,
            dtype=np.float32,
        )

        mean_probabilities = matrix.mean(
            axis=0
        )

        probability_dict = {
            class_name: float(probability)
            for class_name, probability in zip(
                self.config.classes,
                mean_probabilities,
            )
        }

        result = self._build_prediction(
            probability_dict
        )

        result.metadata.update(
            {
                "num_patches": len(
                    patch_predictions
                ),
                "aggregation": "mean",
            }
        )

        return result

    # ---------------------------------------------------------------------
    # WEIGHTED PATCH AGGREGATION
    # ---------------------------------------------------------------------

    def aggregate_weighted(
        self,
        patch_predictions: Sequence[
            PatchPrediction
        ],
        weights: Optional[np.ndarray] = None,
    ) -> PathologyPrediction:
        """
        Ważona agregacja patchy.

        Przydatne, kiedy np.:
        - patchy z centrum zmiany mają większą wagę,
        - attention model nadaje różne wagi,
        - patchy mają różną jakość.
        """

        if len(patch_predictions) == 0:

            raise ValueError(
                "Brak patchy."
            )

        matrix = np.asarray(
            [
                [
                    _normalize_probabilities(
                        p.probabilities,
                        self.config.classes,
                    )[class_name]
                    for class_name in self.config.classes
                ]
                for p in patch_predictions
            ],
            dtype=np.float32,
        )

        if weights is None:

            weights = np.ones(
                len(patch_predictions),
                dtype=np.float32,
            )

        weights = np.asarray(
            weights,
            dtype=np.float32,
        )

        if len(weights) != len(
            patch_predictions
        ):
            raise ValueError(
                "Liczba wag musi odpowiadać "
                "liczbie patchy."
            )

        if np.any(weights < 0):
            raise ValueError(
                "Wagi nie mogą być ujemne."
            )

        total_weight = float(
            weights.sum()
        )

        if total_weight <= 0:
            raise ValueError(
                "Suma wag musi być większa od 0."
            )

        weights = weights / total_weight

        aggregated = np.sum(
            matrix * weights[:, None],
            axis=0,
        )

        probability_dict = {
            class_name: float(probability)
            for class_name, probability in zip(
                self.config.classes,
                aggregated,
            )
        }

        result = self._build_prediction(
            probability_dict
        )

        result.metadata.update(
            {
                "num_patches": len(
                    patch_predictions
                ),
                "aggregation": "weighted_mean",
            }
        )

        return result

    # ---------------------------------------------------------------------
    # RISK SCORE
    # ---------------------------------------------------------------------

    def calculate_risk_score(
        self,
        probabilities: Dict[str, float],
    ) -> float:
        """
        Wylicza uproszczony score patologiczny.

        Ważne:
        To NIE jest kliniczny score ryzyka.

        Jest to wewnętrzna reprezentacja modelowa,
        którą później może wykorzystać risk_model.py.
        """

        probabilities = _normalize_probabilities(
            probabilities,
            self.config.classes,
        )

        score = 0.0

        score += (
            probabilities.get(
                "melanoma",
                0.0,
            )
            * self.config.melanoma_weight
        )

        score += (
            probabilities.get(
                "bcc",
                0.0,
            )
            * self.config.bcc_weight
        )

        score += (
            probabilities.get(
                "other_lesion",
                0.0,
            )
            * self.config.other_lesion_weight
        )

        return float(
            np.clip(score, 0.0, 1.0)
        )

    # ---------------------------------------------------------------------
    # ABNORMALITY
    # ---------------------------------------------------------------------

    def is_abnormal(
        self,
        probabilities: Dict[str, float],
    ) -> bool:
        """
        Określa, czy przypadek jest patologicznie nieprawidłowy.
        """

        probabilities = _normalize_probabilities(
            probabilities,
            self.config.classes,
        )

        abnormal_probability = (
            1.0
            - probabilities.get(
                "normal",
                0.0,
            )
        )

        return (
            abnormal_probability
            >= self.config.abnormal_threshold
        )

    # ---------------------------------------------------------------------
    # INTERNAL PREDICTION BUILDER
    # ---------------------------------------------------------------------

    def _build_prediction(
        self,
        probabilities: Dict[str, float],
    ) -> PathologyPrediction:
        """
        Buduje obiekt PathologyPrediction.
        """

        probabilities = _normalize_probabilities(
            probabilities,
            self.config.classes,
        )

        label = max(
            probabilities,
            key=probabilities.get,
        )

        confidence = float(
            probabilities[label]
        )

        abnormal = self.is_abnormal(
            probabilities
        )

        risk_score = self.calculate_risk_score(
            probabilities
        )

        return PathologyPrediction(
            label=label,
            probabilities=probabilities,
            confidence=confidence,
            abnormal=abnormal,
            risk_score=risk_score,
        )

    # ---------------------------------------------------------------------
    # SUMMARY
    # ---------------------------------------------------------------------

    def summarize(
        self,
        prediction: PathologyPrediction,
    ) -> Dict:
        """
        Tworzy prosty podsumowujący słownik.
        """

        return {
            "diagnosis": prediction.label,
            "confidence": round(
                prediction.confidence,
                4,
            ),
            "abnormal": prediction.abnormal,
            "risk_score": round(
                prediction.risk_score,
                4,
            ),
            "high_risk": (
                prediction.risk_score
                >= self.config.high_risk_threshold
            ),
            "probabilities": {
                key: round(value, 4)
                for key, value in (
                    prediction.probabilities.items()
                )
            },
        }


# ============================================================================
# PATHOLOGY FEATURE AGGREGATOR
# ============================================================================

class PathologyFeatureAggregator:
    """
    Agreguje wyniki patologii do wektora cech.

    Ten komponent jest szczególnie ważny dla:

        pathology_model
                |
                v
        pathology features
                |
                v
        fusion_model

    Dzięki temu fusion_model nie musi znać szczegółów
    działania klasyfikatora patologicznego.
    """

    def __init__(
        self,
        classes: Sequence[str] = DEFAULT_CLASSES,
    ) -> None:

        self.classes = tuple(classes)

    def prediction_to_vector(
        self,
        prediction: PathologyPrediction,
    ) -> np.ndarray:
        """
        Zamienia predykcję na wektor numeryczny.

        Format:

        [
            P(normal),
            P(bcc),
            P(melanoma),
            P(other_lesion),
            confidence,
            abnormal,
            risk_score
        ]
        """

        vector = [
            prediction.probabilities.get(
                class_name,
                0.0,
            )
            for class_name in self.classes
        ]

        vector.extend(
            [
                prediction.confidence,
                float(prediction.abnormal),
                prediction.risk_score,
            ]
        )

        return np.asarray(
            vector,
            dtype=np.float32,
        )

    @property
    def output_dim(self) -> int:
        return len(self.classes) + 3


# ============================================================================
# MULTI-SAMPLE ANALYSIS
# ============================================================================

class PathologyAnalyzer:
    """
    Wyższy poziom analizy wielu przypadków.

    Przydatne np. podczas:
    - ewaluacji datasetu,
    - analizy kohorty,
    - generowania statystyk,
    - przygotowania danych treningowych.
    """

    def __init__(
        self,
        model: PathologyModel,
    ) -> None:

        self.model = model

    def analyze_predictions(
        self,
        predictions: Sequence[
            PathologyPrediction
        ],
    ) -> Dict:
        """
        Analizuje rozkład predykcji w kohorcie.
        """

        if not predictions:

            return {
                "num_samples": 0,
                "class_distribution": {},
                "mean_risk_score": 0.0,
                "abnormal_fraction": 0.0,
            }

        class_counts = {
            class_name: 0
            for class_name in self.model.config.classes
        }

        risk_scores = []
        abnormal_count = 0

        for prediction in predictions:

            class_counts[
                prediction.label
            ] += 1

            risk_scores.append(
                prediction.risk_score
            )

            if prediction.abnormal:
                abnormal_count += 1

        num_samples = len(predictions)

        class_distribution = {
            class_name: count / num_samples
            for class_name, count in class_counts.items()
        }

        return {
            "num_samples": num_samples,
            "class_counts": class_counts,
            "class_distribution": class_distribution,
            "mean_risk_score": float(
                np.mean(risk_scores)
            ),
            "median_risk_score": float(
                np.median(risk_scores)
            ),
            "abnormal_fraction": (
                abnormal_count / num_samples
            ),
        }


# ============================================================================
# FACTORY
# ============================================================================

def create_pathology_model(
    embedding_dim: int = 768,
    device: Optional[str] = None,
    checkpoint_path: Optional[str] = None,
    classes: Sequence[str] = DEFAULT_CLASSES,
) -> PathologyModel:
    """
    Factory function tworząca PathologyModel.

    Przykład:

        model = create_pathology_model(
            embedding_dim=768,
            checkpoint_path="models/checkpoints/pathology/model.pt"
        )
    """

    config = PathologyConfig(
        classes=tuple(classes)
    )

    model = PathologyModel(
        embedding_dim=embedding_dim,
        config=config,
        device=device,
    )

    if checkpoint_path is not None:

        model.load_checkpoint(
            checkpoint_path
        )

    return model


# ============================================================================
# SIMPLE TEST
# ============================================================================

if __name__ == "__main__":

    print("=" * 70)
    print("Pathology Model")
    print("=" * 70)

    if torch is None:

        print(
            "PyTorch nie jest zainstalowany."
        )

    else:

        model = create_pathology_model(
            embedding_dim=768
        )

        # Przykładowy embedding DINOv2.
        dummy_embedding = np.random.randn(
            768
        ).astype(
            np.float32
        )

        prediction = model.predict_embedding(
            dummy_embedding
        )

        print("\nPrediction:")
        print(
            prediction.to_dict()
        )

        print("\nSummary:")
        print(
            model.summarize(
                prediction
            )
        )

        aggregator = PathologyFeatureAggregator()

        features = aggregator.prediction_to_vector(
            prediction
        )

        print("\nFeature vector:")
        print(
            features
        )

        print(
            "\nFeature dimension:",
            aggregator.output_dim,
        )