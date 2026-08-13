
"""
hand_pipeline.py

Pipeline przetwarzania danych dłoni.

Odpowiedzialność:
    1. Wczytywanie obrazów i klatek wideo.
    2. Detekcja dłoni.
    3. Ekstrakcja landmarków przez MediaPipe.
    4. Normalizacja współrzędnych.
    5. Ekstrakcja podstawowych cech geometrycznych.
    6. Opcjonalna integracja z modelem MANO.
    7. Zapis wyników do data/processed/.
    8. Przygotowanie danych dla:
       - hand_model.py
       - morphology_analysis.py
       - aging_model.py
       - fusion_model.py
       - longitudinal_pipeline.py

Pipeline NIE wykonuje treningu modelu.
"""

from __future__ import annotations

import json
import logging
import math
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple

import numpy as np
from PIL import Image


# ---------------------------------------------------------------------
# Optional dependencies
# ---------------------------------------------------------------------

try:
    import cv2
except ImportError:
    cv2 = None


try:
    import mediapipe as mp
except ImportError:
    mp = None


# ---------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------

NUM_HAND_LANDMARKS = 21

# MediaPipe hand landmark indices
WRIST = 0

THUMB_CMC = 1
THUMB_MCP = 2
THUMB_IP = 3
THUMB_TIP = 4

INDEX_MCP = 5
INDEX_PIP = 6
INDEX_DIP = 7
INDEX_TIP = 8

MIDDLE_MCP = 9
MIDDLE_PIP = 10
MIDDLE_DIP = 11
MIDDLE_TIP = 12

RING_MCP = 13
RING_PIP = 14
RING_DIP = 15
RING_TIP = 16

PINKY_MCP = 17
PINKY_PIP = 18
PINKY_DIP = 19
PINKY_TIP = 20


# ---------------------------------------------------------------------
# Dataclasses
# ---------------------------------------------------------------------

@dataclass
class Landmark:
    """
    Pojedynczy landmark dłoni.

    x, y:
        współrzędne znormalizowane względem obrazu.

    z:
        względna współrzędna głębokości MediaPipe.
    """

    index: int
    x: float
    y: float
    z: float
    visibility: float = 1.0


@dataclass
class HandFeatures:
    """
    Podstawowe cechy geometryczne jednej dłoni.
    """

    hand_index: int

    handedness: str

    wrist_to_index_tip: float
    wrist_to_middle_tip: float
    wrist_to_ring_tip: float
    wrist_to_pinky_tip: float
    wrist_to_thumb_tip: float

    palm_width: float
    palm_length: float

    thumb_length: float
    index_length: float
    middle_length: float
    ring_length: float
    pinky_length: float

    hand_width: float
    hand_height: float

    finger_spread_index_middle: float
    finger_spread_middle_ring: float
    finger_spread_ring_pinky: float

    mean_landmark_x: float
    mean_landmark_y: float
    mean_landmark_z: float


@dataclass
class HandResult:
    """
    Wynik analizy jednej klatki/obrazu.
    """

    source_path: str

    image_width: int
    image_height: int

    num_hands: int

    landmarks: List[List[Landmark]]

    features: List[HandFeatures]

    handedness: List[str]

    mano_output: Optional[Dict[str, Any]] = None


@dataclass
class HandPipelineResult:
    """
    Wynik przetwarzania jednego źródła.
    """

    source_path: str

    frames_processed: int

    hands_detected: int

    output_path: Optional[str]

    results: List[HandResult]


# ---------------------------------------------------------------------
# Utility functions
# ---------------------------------------------------------------------

def load_image(path: Path) -> np.ndarray:
    """
    Wczytuje obraz RGB.
    """

    if not path.exists():
        raise FileNotFoundError(
            f"Image not found: {path}"
        )

    image = Image.open(path).convert("RGB")

    return np.asarray(image)


def save_json(
    data: Dict[str, Any],
    path: Path,
) -> None:
    """
    Zapisuje strukturę do JSON.
    """

    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with open(
        path,
        "w",
        encoding="utf-8",
    ) as f:

        json.dump(
            data,
            f,
            indent=2,
            ensure_ascii=False,
        )


def euclidean_distance(
    p1: Sequence[float],
    p2: Sequence[float],
) -> float:
    """
    Odległość euklidesowa dwóch punktów.
    """

    return float(
        np.linalg.norm(
            np.asarray(p1, dtype=np.float32)
            -
            np.asarray(p2, dtype=np.float32)
        )
    )


def landmark_to_array(
    landmark: Landmark,
) -> np.ndarray:
    """
    Konwertuje landmark do wektora [x, y, z].
    """

    return np.array(
        [
            landmark.x,
            landmark.y,
            landmark.z,
        ],
        dtype=np.float32,
    )


# ---------------------------------------------------------------------
# Landmark normalization
# ---------------------------------------------------------------------

def normalize_landmarks(
    landmarks: List[Landmark],
) -> List[Landmark]:
    """
    Normalizuje landmarki względem nadgarstka
    i skali dłoni.

    Dzięki temu późniejsze modele są mniej zależne
    od:
        - odległości dłoni od kamery,
        - rozdzielczości obrazu,
        - wielkości dłoni w kadrze.

    Nadgarstek staje się punktem (0, 0, 0).

    Następnie współrzędne są skalowane przez odległość
    wrist -> middle MCP.
    """

    if len(landmarks) != NUM_HAND_LANDMARKS:
        raise ValueError(
            f"Expected {NUM_HAND_LANDMARKS} landmarks, "
            f"got {len(landmarks)}"
        )

    wrist = landmark_to_array(
        landmarks[WRIST]
    )

    scale = euclidean_distance(
        wrist,
        landmark_to_array(
            landmarks[MIDDLE_MCP]
        ),
    )

    if scale < 1e-8:
        scale = 1.0

    normalized = []

    for landmark in landmarks:

        point = (
            landmark_to_array(landmark)
            - wrist
        ) / scale

        normalized.append(
            Landmark(
                index=landmark.index,
                x=float(point[0]),
                y=float(point[1]),
                z=float(point[2]),
                visibility=landmark.visibility,
            )
        )

    return normalized


# ---------------------------------------------------------------------
# Hand geometry
# ---------------------------------------------------------------------

def calculate_hand_features(
    landmarks: List[Landmark],
    hand_index: int,
    handedness: str,
) -> HandFeatures:
    """
    Wylicza podstawowe cechy geometryczne dłoni.
    """

    if len(landmarks) != NUM_HAND_LANDMARKS:
        raise ValueError(
            "Invalid landmark count."
        )

    def point(index: int) -> np.ndarray:
        return landmark_to_array(
            landmarks[index]
        )

    wrist = point(WRIST)

    # ---------------------------------------------------------------
    # Wrist -> fingertip distances
    # ---------------------------------------------------------------

    wrist_to_index = euclidean_distance(
        wrist,
        point(INDEX_TIP),
    )

    wrist_to_middle = euclidean_distance(
        wrist,
        point(MIDDLE_TIP),
    )

    wrist_to_ring = euclidean_distance(
        wrist,
        point(RING_TIP),
    )

    wrist_to_pinky = euclidean_distance(
        wrist,
        point(PINKY_TIP),
    )

    wrist_to_thumb = euclidean_distance(
        wrist,
        point(THUMB_TIP),
    )

    # ---------------------------------------------------------------
    # Palm geometry
    # ---------------------------------------------------------------

    palm_width = euclidean_distance(
        point(INDEX_MCP),
        point(PINKY_MCP),
    )

    palm_length = euclidean_distance(
        point(WRIST),
        point(MIDDLE_MCP),
    )

    # ---------------------------------------------------------------
    # Finger lengths
    # ---------------------------------------------------------------

    thumb_length = (
        euclidean_distance(
            point(THUMB_CMC),
            point(THUMB_MCP),
        )
        +
        euclidean_distance(
            point(THUMB_MCP),
            point(THUMB_IP),
        )
        +
        euclidean_distance(
            point(THUMB_IP),
            point(THUMB_TIP),
        )
    )

    index_length = (
        euclidean_distance(
            point(INDEX_MCP),
            point(INDEX_PIP),
        )
        +
        euclidean_distance(
            point(INDEX_PIP),
            point(INDEX_DIP),
        )
        +
        euclidean_distance(
            point(INDEX_DIP),
            point(INDEX_TIP),
        )
    )

    middle_length = (
        euclidean_distance(
            point(MIDDLE_MCP),
            point(MIDDLE_PIP),
        )
        +
        euclidean_distance(
            point(MIDDLE_PIP),
            point(MIDDLE_DIP),
        )
        +
        euclidean_distance(
            point(MIDDLE_DIP),
            point(MIDDLE_TIP),
        )
    )

    ring_length = (
        euclidean_distance(
            point(RING_MCP),
            point(RING_PIP),
        )
        +
        euclidean_distance(
            point(RING_PIP),
            point(RING_DIP),
        )
        +
        euclidean_distance(
            point(RING_DIP),
            point(RING_TIP),
        )
    )

    pinky_length = (
        euclidean_distance(
            point(PINKY_MCP),
            point(PINKY_PIP),
        )
        +
        euclidean_distance(
            point(PINKY_PIP),
            point(PINKY_DIP),
        )
        +
        euclidean_distance(
            point(PINKY_DIP),
            point(PINKY_TIP),
        )
    )

    # ---------------------------------------------------------------
    # Bounding box
    # ---------------------------------------------------------------

    all_points = np.stack(
        [
            point(i)
            for i in range(NUM_HAND_LANDMARKS)
        ],
        axis=0,
    )

    x_min = float(all_points[:, 0].min())
    x_max = float(all_points[:, 0].max())

    y_min = float(all_points[:, 1].min())
    y_max = float(all_points[:, 1].max())

    hand_width = x_max - x_min
    hand_height = y_max - y_min

    # ---------------------------------------------------------------
    # Finger spread
    # ---------------------------------------------------------------

    spread_index_middle = euclidean_distance(
        point(INDEX_TIP),
        point(MIDDLE_TIP),
    )

    spread_middle_ring = euclidean_distance(
        point(MIDDLE_TIP),
        point(RING_TIP),
    )

    spread_ring_pinky = euclidean_distance(
        point(RING_TIP),
        point(PINKY_TIP),
    )

    # ---------------------------------------------------------------
    # Global landmark statistics
    # ---------------------------------------------------------------

    mean_x = float(
        all_points[:, 0].mean()
    )

    mean_y = float(
        all_points[:, 1].mean()
    )

    mean_z = float(
        all_points[:, 2].mean()
    )

    return HandFeatures(
        hand_index=hand_index,

        handedness=handedness,

        wrist_to_index_tip=wrist_to_index,
        wrist_to_middle_tip=wrist_to_middle,
        wrist_to_ring_tip=wrist_to_ring,
        wrist_to_pinky_tip=wrist_to_pinky,
        wrist_to_thumb_tip=wrist_to_thumb,

        palm_width=palm_width,
        palm_length=palm_length,

        thumb_length=thumb_length,
        index_length=index_length,
        middle_length=middle_length,
        ring_length=ring_length,
        pinky_length=pinky_length,

        hand_width=hand_width,
        hand_height=hand_height,

        finger_spread_index_middle=spread_index_middle,
        finger_spread_middle_ring=spread_middle_ring,
        finger_spread_ring_pinky=spread_ring_pinky,

        mean_landmark_x=mean_x,
        mean_landmark_y=mean_y,
        mean_landmark_z=mean_z,
    )


# ---------------------------------------------------------------------
# MediaPipe detector
# ---------------------------------------------------------------------

class MediaPipeHandDetector:
    """
    Wrapper dla MediaPipe Hands.

    Jeżeli MediaPipe nie jest zainstalowane,
    pipeline zgłosi czytelny błąd.
    """

    def __init__(
        self,
        max_num_hands: int = 2,
        min_detection_confidence: float = 0.5,
        min_tracking_confidence: float = 0.5,
    ) -> None:

        if mp is None:
            raise ImportError(
                "MediaPipe is not installed. "
                "Install it with: pip install mediapipe"
            )

        self.max_num_hands = max_num_hands

        self.min_detection_confidence = (
            min_detection_confidence
        )

        self.min_tracking_confidence = (
            min_tracking_confidence
        )

        self._hands = None

        self._initialize()

    def _initialize(self) -> None:
        """
        Inicjalizuje MediaPipe Hands.
        """

        self._hands = (
            mp.solutions.hands.Hands(
                static_image_mode=True,
                max_num_hands=self.max_num_hands,
                min_detection_confidence=(
                    self.min_detection_confidence
                ),
                min_tracking_confidence=(
                    self.min_tracking_confidence
                ),
            )
        )

    def detect(
        self,
        image: np.ndarray,
    ) -> Tuple[
        List[List[Landmark]],
        List[str],
    ]:
        """
        Detekuje dłonie na obrazie.
        """

        if image.ndim != 3:
            raise ValueError(
                "Expected RGB image with shape H x W x 3."
            )

        if image.shape[2] != 3:
            raise ValueError(
                "Expected RGB image."
            )

        results = self._hands.process(
            image
        )

        if (
            results.multi_hand_landmarks is None
            or results.multi_handedness is None
        ):
            return [], []

        all_landmarks: List[List[Landmark]] = []
        handedness: List[str] = []

        for hand_landmarks, hand_label in zip(
            results.multi_hand_landmarks,
            results.multi_handedness,
        ):

            landmarks = []

            for index, landmark in enumerate(
                hand_landmarks.landmark
            ):

                landmarks.append(
                    Landmark(
                        index=index,
                        x=float(landmark.x),
                        y=float(landmark.y),
                        z=float(landmark.z),
                        visibility=1.0,
                    )
                )

            all_landmarks.append(
                landmarks
            )

            handedness.append(
                hand_label.classification[0].label
            )

        return (
            all_landmarks,
            handedness,
        )

    def close(self) -> None:
        """
        Zwalnia zasoby MediaPipe.
        """

        if self._hands is not None:
            self._hands.close()


# ---------------------------------------------------------------------
# MANO adapter
# ---------------------------------------------------------------------

class MANOAdapter:
    """
    Adapter dla opcjonalnego modelu MANO.

    MANO nie jest tutaj implementowane od zera.

    Adapter pozwala podłączyć później:
        models/hand_model.py

    lub bezpośrednio model MANO znajdujący się w:

        models/checkpoints/mano/

    Oczekiwany interfejs:

        model.predict(landmarks)

    albo:

        model.forward(landmarks)
    """

    def __init__(
        self,
        model: Optional[Any] = None,
    ) -> None:

        self.model = model

    @property
    def available(self) -> bool:
        return self.model is not None

    def predict(
        self,
        landmarks: List[Landmark],
    ) -> Optional[Dict[str, Any]]:
        """
        Wykonuje opcjonalną rekonstrukcję MANO.
        """

        if self.model is None:
            return None

        points = np.array(
            [
                [
                    landmark.x,
                    landmark.y,
                    landmark.z,
                ]
                for landmark in landmarks
            ],
            dtype=np.float32,
        )

        if hasattr(
            self.model,
            "predict",
        ):

            output = self.model.predict(
                points
            )

        elif hasattr(
            self.model,
            "forward",
        ):

            output = self.model.forward(
                points
            )

        else:

            raise AttributeError(
                "MANO model must provide "
                "'predict()' or 'forward()'."
            )

        return self._serialize_output(
            output
        )

    @staticmethod
    def _serialize_output(
        output: Any,
    ) -> Dict[str, Any]:
        """
        Konwertuje podstawowe typy NumPy/PyTorch
        do formatu JSON.
        """

        if output is None:
            return {}

        if isinstance(
            output,
            dict,
        ):

            return {
                key: MANOAdapter._to_serializable(
                    value
                )
                for key, value in output.items()
            }

        return {
            "output":
                MANOAdapter._to_serializable(
                    output
                )
        }

    @staticmethod
    def _to_serializable(
        value: Any,
    ) -> Any:

        if isinstance(
            value,
            np.ndarray,
        ):
            return value.tolist()

        if hasattr(
            value,
            "detach",
        ):

            return (
                value.detach()
                .cpu()
                .numpy()
                .tolist()
            )

        if isinstance(
            value,
            (
                np.float32,
                np.float64,
            ),
        ):

            return float(value)

        if isinstance(
            value,
            (
                np.int32,
                np.int64,
            ),
        ):

            return int(value)

        if isinstance(
            value,
            (
                list,
                tuple,
            ),
        ):

            return [
                MANOAdapter._to_serializable(
                    x
                )
                for x in value
            ]

        return value


# ---------------------------------------------------------------------
# Main pipeline
# ---------------------------------------------------------------------

class HandPipeline:
    """
    Główny pipeline dłoni.

    Przepływ:

        image
          ↓
        MediaPipe
          ↓
        21 landmarks
          ↓
        normalization
          ↓
        geometric features
          ↓
        optional MANO
          ↓
        processed data
    """

    SUPPORTED_EXTENSIONS = {
        ".jpg",
        ".jpeg",
        ".png",
        ".bmp",
        ".tif",
        ".tiff",
        ".webp",
    }

    def __init__(
        self,
        output_dir: str | Path = "data/processed/images",
        detector: Optional[Any] = None,
        mano_adapter: Optional[MANOAdapter] = None,
        max_num_hands: int = 2,
        min_detection_confidence: float = 0.5,
        min_tracking_confidence: float = 0.5,
    ) -> None:

        self.output_dir = Path(
            output_dir
        )

        if detector is not None:

            self.detector = detector

        else:

            self.detector = MediaPipeHandDetector(
                max_num_hands=max_num_hands,
                min_detection_confidence=(
                    min_detection_confidence
                ),
                min_tracking_confidence=(
                    min_tracking_confidence
                ),
            )

        self.mano = (
            mano_adapter
            if mano_adapter is not None
            else MANOAdapter()
        )

        logger.info(
            "HandPipeline initialized. output=%s",
            self.output_dir,
        )

    # -----------------------------------------------------------------
    # Process one image
    # -----------------------------------------------------------------

    def process_image(
        self,
        image_path: str | Path,
        save_outputs: bool = True,
        normalize: bool = True,
    ) -> HandResult:

        image_path = Path(
            image_path
        )

        logger.info(
            "Processing hand image: %s",
            image_path,
        )

        image = load_image(
            image_path
        )

        height, width = image.shape[:2]

        # -------------------------------------------------------------
        # 1. MediaPipe detection
        # -------------------------------------------------------------

        detected_landmarks, handedness = (
            self.detector.detect(
                image
            )
        )

        processed_landmarks = []

        feature_list = []

        mano_outputs = []

        # -------------------------------------------------------------
        # 2. Process every detected hand
        # -------------------------------------------------------------

        for hand_index, (
            landmarks,
            hand_label,
        ) in enumerate(
            zip(
                detected_landmarks,
                handedness,
            )
        ):

            if normalize:

                landmarks_processed = (
                    normalize_landmarks(
                        landmarks
                    )
                )

            else:

                landmarks_processed = landmarks

            processed_landmarks.append(
                landmarks_processed
            )

            # ---------------------------------------------------------
            # 3. Geometry
            # ---------------------------------------------------------

            features = calculate_hand_features(
                landmarks=landmarks_processed,
                hand_index=hand_index,
                handedness=hand_label,
            )

            feature_list.append(
                features
            )

            # ---------------------------------------------------------
            # 4. Optional MANO
            # ---------------------------------------------------------

            mano_output = self.mano.predict(
                landmarks_processed
            )

            if mano_output is not None:

                mano_outputs.append(
                    mano_output
                )

        # -------------------------------------------------------------
        # 5. Result
        # -------------------------------------------------------------

        mano_result = (
            {
                "hands": mano_outputs
            }
            if mano_outputs
            else None
        )

        result = HandResult(
            source_path=str(
                image_path
            ),

            image_width=width,
            image_height=height,

            num_hands=len(
                processed_landmarks
            ),

            landmarks=processed_landmarks,

            features=feature_list,

            handedness=handedness,

            mano_output=mano_result,
        )

        # -------------------------------------------------------------
        # 6. Save
        # -------------------------------------------------------------

        if save_outputs:

            self._save_result(
                result
            )

        logger.info(
            "Detected %d hands in %s",
            result.num_hands,
            image_path.name,
        )

        return result

    # -----------------------------------------------------------------
    # Save
    # -----------------------------------------------------------------

    def _save_result(
        self,
        result: HandResult,
    ) -> Path:

        source = Path(
            result.source_path
        )

        output_path = (
            self.output_dir
            / "hands"
            / f"{source.stem}_hands.json"
        )

        serializable = {
            "source_path":
                result.source_path,

            "image_width":
                result.image_width,

            "image_height":
                result.image_height,

            "num_hands":
                result.num_hands,

            "handedness":
                result.handedness,

            "landmarks": [
                [
                    asdict(
                        landmark
                    )
                    for landmark in hand
                ]
                for hand in result.landmarks
            ],

            "features": [
                asdict(
                    feature
                )
                for feature in result.features
            ],

            "mano_output":
                result.mano_output,
        }

        save_json(
            serializable,
            output_path,
        )

        return output_path

    # -----------------------------------------------------------------
    # Directory
    # -----------------------------------------------------------------

    def find_images(
        self,
        input_dir: str | Path,
    ) -> List[Path]:

        input_dir = Path(
            input_dir
        )

        if not input_dir.exists():

            raise FileNotFoundError(
                f"Input directory not found: "
                f"{input_dir}"
            )

        images = [
            path
            for path in input_dir.rglob("*")
            if (
                path.is_file()
                and path.suffix.lower()
                in self.SUPPORTED_EXTENSIONS
            )
        ]

        return sorted(
            images
        )

    def process_directory(
        self,
        input_dir: str | Path,
        save_outputs: bool = True,
    ) -> List[HandResult]:

        images = self.find_images(
            input_dir
        )

        logger.info(
            "Found %d hand images.",
            len(images),
        )

        results = []

        for image_path in images:

            try:

                result = self.process_image(
                    image_path=image_path,
                    save_outputs=save_outputs,
                )

                results.append(
                    result
                )

            except Exception as exc:

                logger.exception(
                    "Failed to process %s: %s",
                    image_path,
                    exc,
                )

        return results

    # -----------------------------------------------------------------
    # Summary
    # -----------------------------------------------------------------

    @staticmethod
    def summarize(
        results: Sequence[HandResult],
    ) -> Dict[str, Any]:

        images_processed = len(
            results
        )

        total_hands = sum(
            result.num_hands
            for result in results
        )

        images_with_hands = sum(
            1
            for result in results
            if result.num_hands > 0
        )

        mean_hands_per_image = (
            total_hands / images_processed
            if images_processed > 0
            else 0.0
        )

        return {
            "images_processed":
                images_processed,

            "images_with_hands":
                images_with_hands,

            "total_hands":
                total_hands,

            "mean_hands_per_image":
                mean_hands_per_image,
        }


# ---------------------------------------------------------------------
# Convenience API
# ---------------------------------------------------------------------

def run_hand_pipeline(
    input_path: str | Path,
    output_dir: str | Path = "data/processed/images",
    mano_model: Optional[Any] = None,
) -> Dict[str, Any]:
    """
    Uruchamia pipeline na obrazie lub katalogu.
    """

    mano_adapter = MANOAdapter(
        model=mano_model
    )

    pipeline = HandPipeline(
        output_dir=output_dir,
        mano_adapter=mano_adapter,
    )

    input_path = Path(
        input_path
    )

    if input_path.is_file():

        result = pipeline.process_image(
            input_path
        )

        return {
            "mode": "single_image",

            "summary":
                pipeline.summarize(
                    [result]
                ),

            "results":
                [result],
        }

    if input_path.is_dir():

        results = (
            pipeline.process_directory(
                input_path
            )
        )

        return {
            "mode": "directory",

            "summary":
                pipeline.summarize(
                    results
                ),

            "results":
                results,
        }

    raise FileNotFoundError(
        f"Input path does not exist: "
        f"{input_path}"
    )


# ---------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------

def main() -> None:
    """
    Przykłady:

        python pipeline/hand_pipeline.py \
            --input data/raw/hand/media

    albo:

        python pipeline/hand_pipeline.py \
            --input data/raw/hand/InterHand2.6M
    """

    import argparse

    parser = argparse.ArgumentParser(
        description=(
            "Hand processing pipeline using "
            "MediaPipe and optional MANO."
        )
    )

    parser.add_argument(
        "--input",
        required=True,
        help=(
            "Input image or directory."
        ),
    )

    parser.add_argument(
        "--output",
        default=(
            "data/processed/images"
        ),
        help=(
            "Output directory."
        ),
    )

    args = parser.parse_args()

    logging.basicConfig(
        level=logging.INFO,
        format=(
            "%(asctime)s | "
            "%(levelname)s | "
            "%(name)s | "
            "%(message)s"
        ),
    )

    summary = run_hand_pipeline(
        input_path=args.input,
        output_dir=args.output,
    )

    print()
    print("Hand pipeline summary")
    print("---------------------")

    for key, value in (
        summary["summary"].items()
    ):

        print(
            f"{key}: {value}"
        )


if __name__ == "__main__":
    main()

