# models/digital_twin.py

"""
Digital Twin model.

This module provides a research-oriented digital twin representation
for longitudinal multimodal skin analysis.

The digital twin combines:
    - image-derived features
    - tissue features
    - cellular features
    - RNA / transcriptomic features
    - hand / morphology features
    - biological-age estimates
    - abnormality estimates
    - pathology estimates
    - risk estimates
    - longitudinal observations

Important:
    This module is intended for research and modelling purposes.
    It does not provide medical diagnosis, treatment recommendations,
    or autonomous clinical decisions.
"""

from __future__ import annotations

from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Any, Dict, List, Optional, Sequence, Tuple
import copy
import json
import logging
import math

import numpy as np


logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------
# Utility functions
# ---------------------------------------------------------------------


def _safe_float(value: Any, default: float = 0.0) -> float:
    """Convert a value to float safely."""
    try:
        value = float(value)

        if not math.isfinite(value):
            return default

        return value

    except (TypeError, ValueError):
        return default


def _clip(value: float, low: float = 0.0, high: float = 1.0) -> float:
    """Clip a scalar to a specified interval."""
    return max(low, min(high, value))


def _to_numpy(
    value: Optional[Sequence[float]],
    dtype: np.dtype = np.float32,
) -> Optional[np.ndarray]:
    """Convert sequence-like data to a numpy array."""
    if value is None:
        return None

    array = np.asarray(value, dtype=dtype)

    if array.size == 0:
        return None

    return array


def _normalize_vector(
    vector: Optional[np.ndarray],
) -> Optional[np.ndarray]:
    """L2-normalize a vector."""
    if vector is None:
        return None

    norm = np.linalg.norm(vector)

    if norm <= 1e-12:
        return vector.copy()

    return vector / norm


def _cosine_similarity(
    a: Optional[np.ndarray],
    b: Optional[np.ndarray],
) -> Optional[float]:
    """Compute cosine similarity between two vectors."""
    if a is None or b is None:
        return None

    a = np.asarray(a, dtype=np.float32).reshape(-1)
    b = np.asarray(b, dtype=np.float32).reshape(-1)

    if a.shape != b.shape:
        return None

    denom = np.linalg.norm(a) * np.linalg.norm(b)

    if denom <= 1e-12:
        return 0.0

    return float(np.dot(a, b) / denom)


def _mean_available(values: Sequence[Optional[float]]) -> Optional[float]:
    """Mean of available numeric values."""
    valid = [
        _safe_float(v)
        for v in values
        if v is not None
    ]

    if not valid:
        return None

    return float(np.mean(valid))


# ---------------------------------------------------------------------
# Observation
# ---------------------------------------------------------------------


@dataclass
class TwinObservation:
    """
    Single longitudinal observation.

    One observation corresponds to a time point such as:
        T0
        T1
        T2
        T3
    """

    timestamp: str

    image_features: Optional[np.ndarray] = None
    tissue_features: Optional[np.ndarray] = None
    cell_features: Optional[np.ndarray] = None
    rna_features: Optional[np.ndarray] = None
    hand_features: Optional[np.ndarray] = None

    biological_age: Optional[float] = None
    abnormality_score: Optional[float] = None
    pathology_score: Optional[float] = None
    risk_score: Optional[float] = None

    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.image_features = _to_numpy(self.image_features)
        self.tissue_features = _to_numpy(self.tissue_features)
        self.cell_features = _to_numpy(self.cell_features)
        self.rna_features = _to_numpy(self.rna_features)
        self.hand_features = _to_numpy(self.hand_features)

        if self.biological_age is not None:
            self.biological_age = _safe_float(self.biological_age)

        if self.abnormality_score is not None:
            self.abnormality_score = _clip(
                _safe_float(self.abnormality_score)
            )

        if self.pathology_score is not None:
            self.pathology_score = _clip(
                _safe_float(self.pathology_score)
            )

        if self.risk_score is not None:
            self.risk_score = _clip(
                _safe_float(self.risk_score)
            )


# ---------------------------------------------------------------------
# State
# ---------------------------------------------------------------------


@dataclass
class DigitalTwinState:
    """
    Current aggregated state of the digital twin.
    """

    biological_age: Optional[float] = None

    tissue_state: Dict[str, float] = field(default_factory=dict)
    cellular_state: Dict[str, float] = field(default_factory=dict)
    molecular_state: Dict[str, float] = field(default_factory=dict)
    morphology_state: Dict[str, float] = field(default_factory=dict)

    abnormality_score: Optional[float] = None
    pathology_score: Optional[float] = None
    risk_score: Optional[float] = None

    confidence: float = 0.0

    embedding: Optional[np.ndarray] = None

    last_update: Optional[str] = None

    metadata: Dict[str, Any] = field(default_factory=dict)


# ---------------------------------------------------------------------
# Digital Twin
# ---------------------------------------------------------------------


class DigitalTwin:
    """
    Multimodal longitudinal digital twin.

    The object stores:
        1. observations
        2. current state
        3. historical state
        4. derived trajectories
        5. multimodal representation

    Example
    -------
    >>> twin = DigitalTwin(subject_id="subject_001")

    >>> twin.add_observation(
    ...     timestamp="T0",
    ...     image_features=np.random.randn(768),
    ...     tissue_features=np.random.randn(128),
    ...     biological_age=45.2,
    ...     risk_score=0.12,
    ... )

    >>> twin.update_state()

    >>> state = twin.get_state()
    """

    def __init__(
        self,
        subject_id: str,
        embedding_dim: Optional[int] = None,
        max_history: Optional[int] = None,
    ) -> None:

        if not subject_id:
            raise ValueError("subject_id cannot be empty.")

        self.subject_id = subject_id

        self.embedding_dim = embedding_dim
        self.max_history = max_history

        self.observations: List[TwinObservation] = []

        self.state = DigitalTwinState()

        self.state_history: List[DigitalTwinState] = []

        self.created_at = datetime.utcnow().isoformat()

        self.updated_at = self.created_at

    # -----------------------------------------------------------------
    # Observation management
    # -----------------------------------------------------------------

    def add_observation(
        self,
        timestamp: str,
        image_features: Optional[Sequence[float]] = None,
        tissue_features: Optional[Sequence[float]] = None,
        cell_features: Optional[Sequence[float]] = None,
        rna_features: Optional[Sequence[float]] = None,
        hand_features: Optional[Sequence[float]] = None,
        biological_age: Optional[float] = None,
        abnormality_score: Optional[float] = None,
        pathology_score: Optional[float] = None,
        risk_score: Optional[float] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> TwinObservation:
        """
        Add a new longitudinal observation.
        """

        observation = TwinObservation(
            timestamp=timestamp,
            image_features=image_features,
            tissue_features=tissue_features,
            cell_features=cell_features,
            rna_features=rna_features,
            hand_features=hand_features,
            biological_age=biological_age,
            abnormality_score=abnormality_score,
            pathology_score=pathology_score,
            risk_score=risk_score,
            metadata=metadata or {},
        )

        self.observations.append(observation)

        self._sort_observations()

        if self.max_history is not None:
            self.observations = self.observations[-self.max_history:]

        self.updated_at = datetime.utcnow().isoformat()

        logger.info(
            "Added observation %s for subject %s.",
            timestamp,
            self.subject_id,
        )

        return observation

    def _sort_observations(self) -> None:
        """Sort observations chronologically."""
        self.observations.sort(
            key=lambda x: x.timestamp
        )

    # -----------------------------------------------------------------
    # Feature fusion
    # -----------------------------------------------------------------

    def build_multimodal_embedding(
        self,
        observation: Optional[TwinObservation] = None,
        normalize: bool = True,
    ) -> Optional[np.ndarray]:
        """
        Concatenate available modality embeddings.

        This is intentionally a simple baseline fusion mechanism.
        A learned fusion model can later replace this function.
        """

        if observation is None:

            if not self.observations:
                return None

            observation = self.observations[-1]

        features: List[np.ndarray] = []

        modalities = [
            observation.image_features,
            observation.tissue_features,
            observation.cell_features,
            observation.rna_features,
            observation.hand_features,
        ]

        for feature in modalities:

            if feature is None:
                continue

            feature = np.asarray(
                feature,
                dtype=np.float32,
            ).reshape(-1)

            features.append(feature)

        if not features:
            return None

        embedding = np.concatenate(features)

        if normalize:
            embedding = _normalize_vector(embedding)

        return embedding

    # -----------------------------------------------------------------
    # State update
    # -----------------------------------------------------------------

    def update_state(self) -> DigitalTwinState:
        """
        Update the current twin state from the latest observation.
        """

        if not self.observations:
            logger.warning(
                "Cannot update state: no observations available."
            )
            return self.state

        observation = self.observations[-1]

        previous_state = copy.deepcopy(self.state)

        # -------------------------------------------------------------
        # Biological age
        # -------------------------------------------------------------

        self.state.biological_age = (
            observation.biological_age
            if observation.biological_age is not None
            else self.state.biological_age
        )

        # -------------------------------------------------------------
        # Scores
        # -------------------------------------------------------------

        self.state.abnormality_score = (
            observation.abnormality_score
            if observation.abnormality_score is not None
            else self.state.abnormality_score
        )

        self.state.pathology_score = (
            observation.pathology_score
            if observation.pathology_score is not None
            else self.state.pathology_score
        )

        self.state.risk_score = (
            observation.risk_score
            if observation.risk_score is not None
            else self.state.risk_score
        )

        # -------------------------------------------------------------
        # Modality states
        # -------------------------------------------------------------

        self.state.tissue_state = self._summarize_features(
            observation.tissue_features
        )

        self.state.cellular_state = self._summarize_features(
            observation.cell_features
        )

        self.state.molecular_state = self._summarize_features(
            observation.rna_features
        )

        self.state.morphology_state = self._summarize_features(
            observation.hand_features
        )

        # -------------------------------------------------------------
        # Multimodal embedding
        # -------------------------------------------------------------

        embedding = self.build_multimodal_embedding(
            observation
        )

        if embedding is not None:

            self.state.embedding = embedding

        # -------------------------------------------------------------
        # Confidence
        # -------------------------------------------------------------

        self.state.confidence = self._estimate_state_confidence(
            observation
        )

        self.state.last_update = observation.timestamp

        # Save previous state
        self.state_history.append(previous_state)

        self.updated_at = datetime.utcnow().isoformat()

        return self.state

    # -----------------------------------------------------------------
    # Feature summarization
    # -----------------------------------------------------------------

    @staticmethod
    def _summarize_features(
        features: Optional[np.ndarray],
    ) -> Dict[str, float]:
        """
        Create a compact statistical summary of a feature vector.
        """

        if features is None:
            return {}

        features = np.asarray(
            features,
            dtype=np.float32,
        ).reshape(-1)

        if features.size == 0:
            return {}

        finite = features[np.isfinite(features)]

        if finite.size == 0:
            return {}

        return {
            "mean": float(np.mean(finite)),
            "std": float(np.std(finite)),
            "min": float(np.min(finite)),
            "max": float(np.max(finite)),
            "median": float(np.median(finite)),
            "l2_norm": float(np.linalg.norm(finite)),
            "dimension": float(finite.size),
        }

    # -----------------------------------------------------------------
    # Confidence
    # -----------------------------------------------------------------

    def _estimate_state_confidence(
        self,
        observation: TwinObservation,
    ) -> float:
        """
        Estimate confidence from modality availability.

        This is NOT a clinical confidence score.

        It only measures how much multimodal information is available.
        """

        modalities = [
            observation.image_features,
            observation.tissue_features,
            observation.cell_features,
            observation.rna_features,
            observation.hand_features,
        ]

        available_modalities = sum(
            feature is not None
            for feature in modalities
        )

        modality_confidence = (
            available_modalities / len(modalities)
        )

        score_availability = [
            observation.biological_age is not None,
            observation.abnormality_score is not None,
            observation.pathology_score is not None,
            observation.risk_score is not None,
        ]

        score_confidence = (
            sum(score_availability) /
            len(score_availability)
        )

        confidence = (
            0.7 * modality_confidence
            + 0.3 * score_confidence
        )

        return float(_clip(confidence))

    # -----------------------------------------------------------------
    # Longitudinal analysis
    # -----------------------------------------------------------------

    def get_trajectory(
        self,
        attribute: str,
    ) -> List[Tuple[str, Optional[float]]]:
        """
        Return a longitudinal trajectory.

        Supported attributes:
            biological_age
            abnormality_score
            pathology_score
            risk_score
        """

        supported = {
            "biological_age",
            "abnormality_score",
            "pathology_score",
            "risk_score",
        }

        if attribute not in supported:
            raise ValueError(
                f"Unsupported trajectory attribute: {attribute}. "
                f"Supported: {sorted(supported)}"
            )

        return [
            (
                observation.timestamp,
                getattr(observation, attribute),
            )
            for observation in self.observations
        ]

    def get_latest_observation(
        self,
    ) -> Optional[TwinObservation]:
        """Return the most recent observation."""
        if not self.observations:
            return None

        return self.observations[-1]

    def get_previous_observation(
        self,
    ) -> Optional[TwinObservation]:
        """Return the observation immediately before the latest."""
        if len(self.observations) < 2:
            return None

        return self.observations[-2]

    # -----------------------------------------------------------------
    # Change analysis
    # -----------------------------------------------------------------

    def calculate_change(
        self,
        attribute: str,
    ) -> Optional[float]:
        """
        Calculate latest-minus-previous change.
        """

        latest = self.get_latest_observation()
        previous = self.get_previous_observation()

        if latest is None or previous is None:
            return None

        latest_value = getattr(
            latest,
            attribute,
            None,
        )

        previous_value = getattr(
            previous,
            attribute,
            None,
        )

        if latest_value is None or previous_value is None:
            return None

        return float(
            _safe_float(latest_value)
            - _safe_float(previous_value)
        )

    def calculate_relative_change(
        self,
        attribute: str,
    ) -> Optional[float]:
        """
        Calculate relative change between the latest
        and previous observation.
        """

        latest = self.get_latest_observation()
        previous = self.get_previous_observation()

        if latest is None or previous is None:
            return None

        latest_value = getattr(
            latest,
            attribute,
            None,
        )

        previous_value = getattr(
            previous,
            attribute,
            None,
        )

        if latest_value is None or previous_value is None:
            return None

        previous_value = _safe_float(previous_value)

        if abs(previous_value) <= 1e-12:
            return None

        return float(
            (
                _safe_float(latest_value)
                - previous_value
            )
            / abs(previous_value)
        )

    # -----------------------------------------------------------------
    # Embedding trajectory
    # -----------------------------------------------------------------

    def embedding_similarity(
        self,
        index_a: int = -2,
        index_b: int = -1,
    ) -> Optional[float]:
        """
        Compare multimodal embeddings from two observations.
        """

        if len(self.observations) < 2:
            return None

        observation_a = self.observations[index_a]
        observation_b = self.observations[index_b]

        embedding_a = self.build_multimodal_embedding(
            observation_a
        )

        embedding_b = self.build_multimodal_embedding(
            observation_b
        )

        return _cosine_similarity(
            embedding_a,
            embedding_b,
        )

    # -----------------------------------------------------------------
    # State comparison
    # -----------------------------------------------------------------

    def compare_current_to_previous(
        self,
    ) -> Dict[str, Optional[float]]:
        """
        Compare current state with previous observation.
        """

        attributes = [
            "biological_age",
            "abnormality_score",
            "pathology_score",
            "risk_score",
        ]

        result = {}

        for attribute in attributes:

            result[attribute] = self.calculate_change(
                attribute
            )

        result["embedding_similarity"] = (
            self.embedding_similarity()
        )

        return result

    # -----------------------------------------------------------------
    # Longitudinal summary
    # -----------------------------------------------------------------

    def longitudinal_summary(self) -> Dict[str, Any]:
        """
        Generate a compact longitudinal summary.
        """

        if not self.observations:
            return {
                "subject_id": self.subject_id,
                "n_observations": 0,
                "status": "empty",
            }

        summary: Dict[str, Any] = {
            "subject_id": self.subject_id,
            "n_observations": len(self.observations),
            "first_timestamp": self.observations[0].timestamp,
            "last_timestamp": self.observations[-1].timestamp,
        }

        for attribute in [
            "biological_age",
            "abnormality_score",
            "pathology_score",
            "risk_score",
        ]:

            trajectory = self.get_trajectory(
                attribute
            )

            values = [
                value
                for _, value in trajectory
                if value is not None
            ]

            if values:

                summary[attribute] = {
                    "first": float(values[0]),
                    "latest": float(values[-1]),
                    "min": float(np.min(values)),
                    "max": float(np.max(values)),
                    "mean": float(np.mean(values)),
                }

                change = (
                    float(values[-1] - values[0])
                    if len(values) >= 2
                    else None
                )

                summary[attribute]["total_change"] = change

        summary["current_confidence"] = (
            self.state.confidence
        )

        return summary

    # -----------------------------------------------------------------
    # State access
    # -----------------------------------------------------------------

    def get_state(self) -> DigitalTwinState:
        """Return current twin state."""
        return self.state

    # -----------------------------------------------------------------
    # Serialization
    # -----------------------------------------------------------------

    @staticmethod
    def _serialize_array(
        value: Optional[np.ndarray],
    ) -> Optional[List[float]]:
        """Serialize numpy array."""
        if value is None:
            return None

        return np.asarray(
            value,
            dtype=np.float32,
        ).tolist()

    def observation_to_dict(
        self,
        observation: TwinObservation,
    ) -> Dict[str, Any]:
        """Convert observation to JSON-compatible dictionary."""

        return {
            "timestamp": observation.timestamp,

            "image_features": self._serialize_array(
                observation.image_features
            ),

            "tissue_features": self._serialize_array(
                observation.tissue_features
            ),

            "cell_features": self._serialize_array(
                observation.cell_features
            ),

            "rna_features": self._serialize_array(
                observation.rna_features
            ),

            "hand_features": self._serialize_array(
                observation.hand_features
            ),

            "biological_age": observation.biological_age,
            "abnormality_score": observation.abnormality_score,
            "pathology_score": observation.pathology_score,
            "risk_score": observation.risk_score,

            "metadata": observation.metadata,
        }

    def state_to_dict(
        self,
    ) -> Dict[str, Any]:
        """Convert state to JSON-compatible dictionary."""

        state = self.state

        return {
            "biological_age": state.biological_age,

            "tissue_state": state.tissue_state,
            "cellular_state": state.cellular_state,
            "molecular_state": state.molecular_state,
            "morphology_state": state.morphology_state,

            "abnormality_score": state.abnormality_score,
            "pathology_score": state.pathology_score,
            "risk_score": state.risk_score,

            "confidence": state.confidence,

            "embedding": self._serialize_array(
                state.embedding
            ),

            "last_update": state.last_update,

            "metadata": state.metadata,
        }

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the complete digital twin to a dictionary.
        """

        return {
            "subject_id": self.subject_id,
            "created_at": self.created_at,
            "updated_at": self.updated_at,

            "embedding_dim": self.embedding_dim,
            "max_history": self.max_history,

            "observations": [
                self.observation_to_dict(
                    observation
                )
                for observation in self.observations
            ],

            "state": self.state_to_dict(),

            "longitudinal_summary":
                self.longitudinal_summary(),
        }

    def save_json(
        self,
        path: str,
    ) -> None:
        """Save digital twin state to JSON."""

        with open(
            path,
            "w",
            encoding="utf-8",
        ) as file:

            json.dump(
                self.to_dict(),
                file,
                indent=2,
                ensure_ascii=False,
            )

        logger.info(
            "Digital twin saved to %s",
            path,
        )

    # -----------------------------------------------------------------
    # Loading
    # -----------------------------------------------------------------

    @classmethod
    def from_dict(
        cls,
        data: Dict[str, Any],
    ) -> "DigitalTwin":
        """
        Reconstruct a digital twin from a dictionary.
        """

        twin = cls(
            subject_id=data["subject_id"],
            embedding_dim=data.get(
                "embedding_dim"
            ),
            max_history=data.get(
                "max_history"
            ),
        )

        for observation_data in data.get(
            "observations",
            [],
        ):

            twin.add_observation(
                timestamp=observation_data[
                    "timestamp"
                ],

                image_features=observation_data.get(
                    "image_features"
                ),

                tissue_features=observation_data.get(
                    "tissue_features"
                ),

                cell_features=observation_data.get(
                    "cell_features"
                ),

                rna_features=observation_data.get(
                    "rna_features"
                ),

                hand_features=observation_data.get(
                    "hand_features"
                ),

                biological_age=observation_data.get(
                    "biological_age"
                ),

                abnormality_score=observation_data.get(
                    "abnormality_score"
                ),

                pathology_score=observation_data.get(
                    "pathology_score"
                ),

                risk_score=observation_data.get(
                    "risk_score"
                ),

                metadata=observation_data.get(
                    "metadata",
                    {},
                ),
            )

        twin.update_state()

        return twin

    @classmethod
    def load_json(
        cls,
        path: str,
    ) -> "DigitalTwin":
        """Load a digital twin from JSON."""

        with open(
            path,
            "r",
            encoding="utf-8",
        ) as file:

            data = json.load(file)

        return cls.from_dict(data)


# ---------------------------------------------------------------------
# Convenience functions
# ---------------------------------------------------------------------


def create_digital_twin(
    subject_id: str,
    observations: Optional[
        Sequence[Dict[str, Any]]
    ] = None,
) -> DigitalTwin:
    """
    Create and optionally populate a digital twin.
    """

    twin = DigitalTwin(
        subject_id=subject_id
    )

    if observations is not None:

        for observation in observations:

            twin.add_observation(
                **observation
            )

        twin.update_state()

    return twin


def calculate_multimodal_change(
    previous: TwinObservation,
    current: TwinObservation,
) -> Dict[str, Any]:
    """
    Compare two observations across all modalities.
    """

    result: Dict[str, Any] = {}

    modality_pairs = {
        "image": (
            previous.image_features,
            current.image_features,
        ),

        "tissue": (
            previous.tissue_features,
            current.tissue_features,
        ),

        "cell": (
            previous.cell_features,
            current.cell_features,
        ),

        "rna": (
            previous.rna_features,
            current.rna_features,
        ),

        "hand": (
            previous.hand_features,
            current.hand_features,
        ),
    }

    for name, (old, new) in modality_pairs.items():

        similarity = _cosine_similarity(
            old,
            new,
        )

        result[name] = {
            "cosine_similarity": similarity,
        }

        if old is not None and new is not None:

            old = np.asarray(
                old,
                dtype=np.float32,
            ).reshape(-1)

            new = np.asarray(
                new,
                dtype=np.float32,
            ).reshape(-1)

            if old.shape == new.shape:

                delta = new - old

                result[name][
                    "l2_change"
                ] = float(
                    np.linalg.norm(delta)
                )

    score_attributes = [
        "biological_age",
        "abnormality_score",
        "pathology_score",
        "risk_score",
    ]

    for attribute in score_attributes:

        old_value = getattr(
            previous,
            attribute,
            None,
        )

        new_value = getattr(
            current,
            attribute,
            None,
        )

        if (
            old_value is not None
            and new_value is not None
        ):

            result[attribute] = {
                "previous": float(old_value),
                "current": float(new_value),
                "change": float(
                    new_value - old_value
                ),
            }

    return result


# ---------------------------------------------------------------------
# Example
# ---------------------------------------------------------------------

if __name__ == "__main__":

    logging.basicConfig(
        level=logging.INFO
    )

    twin = DigitalTwin(
        subject_id="subject_001"
    )

    # T0
    twin.add_observation(
        timestamp="T0",
        image_features=np.random.randn(768),
        tissue_features=np.random.randn(128),
        cell_features=np.random.randn(64),
        rna_features=np.random.randn(256),
        hand_features=np.random.randn(63),
        biological_age=42.0,
        abnormality_score=0.08,
        pathology_score=0.02,
        risk_score=0.10,
    )

    # T1
    twin.add_observation(
        timestamp="T1",
        image_features=np.random.randn(768),
        tissue_features=np.random.randn(128),
        cell_features=np.random.randn(64),
        rna_features=np.random.randn(256),
        hand_features=np.random.randn(63),
        biological_age=42.7,
        abnormality_score=0.11,
        pathology_score=0.03,
        risk_score=0.14,
    )

    # Update current state
    state = twin.update_state()

    print("Subject:", twin.subject_id)
    print(
        "Biological age:",
        state.biological_age
    )
    print(
        "Risk:",
        state.risk_score
    )
    print(
        "Confidence:",
        state.confidence
    )

    print(
        "\nCurrent vs previous:"
    )

    print(
        twin.compare_current_to_previous()
    )

    print(
        "\nLongitudinal summary:"
    )

    print(
        json.dumps(
            twin.longitudinal_summary(),
            indent=2,
        )
    )