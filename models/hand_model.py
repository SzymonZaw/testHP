"""
models/hand_model.py

Hand analysis module.

Pipeline:
    image
      ↓
    MediaPipe Hand Landmarker
      ↓
    21 hand landmarks
      ↓
    geometric features
      ↓
    optional MANO reconstruction

The module is designed to be used by:
    - pipeline/hand_pipeline.py
    - models/fusion_model.py
    - analysis/morphology_analysis.py
    - models/longitudinal_model.py

Directory structure expected:

models/
├── checkpoints/
│   ├── mano/
│   │   └── ...
│   └── mediapipe/
│       └── hand_landmarker.task
│
└── hand_model.py
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple, Union

import math

import numpy as np


try:
    import torch
except ImportError:
    torch = None


try:
    import cv2
except ImportError:
    cv2 = None


# ---------------------------------------------------------------------------
# Optional MediaPipe import
# ---------------------------------------------------------------------------

try:
    import mediapipe as mp
except ImportError:
    mp = None


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

NUM_HAND_LANDMARKS = 21

LANDMARK_NAMES = [
    "wrist",

    "thumb_cmc",
    "thumb_mcp",
    "thumb_ip",
    "thumb_tip",

    "index_mcp",
    "index_pip",
    "index_dip",
    "index_tip",

    "middle_mcp",
    "middle_pip",
    "middle_dip",
    "middle_tip",

    "ring_mcp",
    "ring_pip",
    "ring_dip",
    "ring_tip",

    "pinky_mcp",
    "pinky_pip",
    "pinky_dip",
    "pinky_tip",
]


# Landmark indices
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


FINGER_LANDMARKS = {
    "thumb": [THUMB_CMC, THUMB_MCP, THUMB_IP, THUMB_TIP],
    "index": [INDEX_MCP, INDEX_PIP, INDEX_DIP, INDEX_TIP],
    "middle": [MIDDLE_MCP, MIDDLE_PIP, MIDDLE_DIP, MIDDLE_TIP],
    "ring": [RING_MCP, RING_PIP, RING_DIP, RING_TIP],
    "pinky": [PINKY_MCP, PINKY_PIP, PINKY_DIP, PINKY_TIP],
}


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------

@dataclass
class HandDetection:
    """
    Result of a single detected hand.
    """

    landmarks: np.ndarray
    """
    Shape:
        (21, 3)

    Coordinates:
        x, y, z

    x/y:
        normalized image coordinates

    z:
        MediaPipe relative depth coordinate
    """

    handedness: Optional[str] = None
    handedness_score: Optional[float] = None

    world_landmarks: Optional[np.ndarray] = None
    """
    Optional shape:
        (21, 3)

    World coordinates in meters when provided by MediaPipe.
    """

    confidence: Optional[float] = None


@dataclass
class HandFeatures:
    """
    Geometry-based hand representation.
    """

    handedness: Optional[str]

    palm_width: float
    palm_length: float

    thumb_length: float
    index_length: float
    middle_length: float
    ring_length: float
    pinky_length: float

    index_mcp_angle: float
    middle_mcp_angle: float
    ring_mcp_angle: float
    pinky_mcp_angle: float

    hand_area: float
    hand_aspect_ratio: float

    fingertip_spread: float

    normalized_landmarks: np.ndarray

    raw_landmarks: np.ndarray


# ---------------------------------------------------------------------------
# Utility functions
# ---------------------------------------------------------------------------

def _as_numpy(
    value: Union[np.ndarray, Sequence[Sequence[float]]]
) -> np.ndarray:
    """
    Convert input to float32 NumPy array.
    """

    array = np.asarray(value, dtype=np.float32)

    return array


def _validate_landmarks(landmarks: np.ndarray) -> None:
    """
    Validate landmark shape.
    """

    if landmarks.ndim != 2:
        raise ValueError(
            f"Landmarks must be 2-dimensional. "
            f"Received shape={landmarks.shape}"
        )

    if landmarks.shape[0] != NUM_HAND_LANDMARKS:
        raise ValueError(
            f"Expected {NUM_HAND_LANDMARKS} landmarks, "
            f"received {landmarks.shape[0]}"
        )

    if landmarks.shape[1] < 2:
        raise ValueError(
            "Landmarks must contain at least x and y coordinates."
        )


def _distance(
    p1: np.ndarray,
    p2: np.ndarray,
) -> float:
    """
    Euclidean distance between two points.
    """

    return float(np.linalg.norm(p1 - p2))


def _angle(
    p1: np.ndarray,
    vertex: np.ndarray,
    p2: np.ndarray,
) -> float:
    """
    Calculate angle p1 -> vertex -> p2 in degrees.
    """

    v1 = p1 - vertex
    v2 = p2 - vertex

    norm1 = np.linalg.norm(v1)
    norm2 = np.linalg.norm(v2)

    if norm1 < 1e-8 or norm2 < 1e-8:
        return 0.0

    cosine = np.dot(v1, v2) / (norm1 * norm2)

    cosine = np.clip(cosine, -1.0, 1.0)

    return float(np.degrees(np.arccos(cosine)))


def _polygon_area(points: np.ndarray) -> float:
    """
    Calculate 2D polygon area using the shoelace formula.
    """

    if len(points) < 3:
        return 0.0

    x = points[:, 0]
    y = points[:, 1]

    return float(
        0.5
        * abs(
            np.dot(x, np.roll(y, -1))
            - np.dot(y, np.roll(x, -1))
        )
    )


# ---------------------------------------------------------------------------
# HandModel
# ---------------------------------------------------------------------------

class HandModel:
    """
    Main hand analysis model.

    Responsibilities:
        1. Load MediaPipe hand detector.
        2. Detect hands.
        3. Extract 21 landmarks.
        4. Normalize landmarks.
        5. Calculate geometric features.
        6. Provide a common representation for downstream models.

    MANO reconstruction is intentionally optional because the exact MANO
    implementation/checkpoint can vary.
    """

    def __init__(
        self,
        checkpoint_dir: Optional[Union[str, Path]] = None,
        mediapipe_model_path: Optional[Union[str, Path]] = None,
        max_num_hands: int = 2,
        min_detection_confidence: float = 0.5,
        min_tracking_confidence: float = 0.5,
        use_mediapipe: bool = True,
        device: Optional[str] = None,
    ) -> None:

        self.checkpoint_dir = (
            Path(checkpoint_dir)
            if checkpoint_dir is not None
            else Path(__file__).resolve().parent / "checkpoints"
        )

        self.mediapipe_checkpoint_dir = (
            self.checkpoint_dir / "mediapipe"
        )

        self.mano_checkpoint_dir = (
            self.checkpoint_dir / "mano"
        )

        self.max_num_hands = max_num_hands

        self.min_detection_confidence = (
            min_detection_confidence
        )

        self.min_tracking_confidence = (
            min_tracking_confidence
        )

        self.device = device or self._default_device()

        self.mediapipe_model_path = (
            Path(mediapipe_model_path)
            if mediapipe_model_path is not None
            else self._find_mediapipe_model()
        )

        self.detector = None

        if use_mediapipe:
            self._initialize_mediapipe()

    # ------------------------------------------------------------------
    # Device
    # ------------------------------------------------------------------

    @staticmethod
    def _default_device() -> str:
        """
        Select CUDA when available, otherwise CPU.
        """

        if torch is not None and torch.cuda.is_available():
            return "cuda"

        return "cpu"

    # ------------------------------------------------------------------
    # Checkpoint discovery
    # ------------------------------------------------------------------

    def _find_mediapipe_model(self) -> Optional[Path]:
        """
        Search for MediaPipe Hand Landmarker model.
        """

        if not self.mediapipe_checkpoint_dir.exists():
            return None

        candidates = list(
            self.mediapipe_checkpoint_dir.rglob("*.task")
        )

        if not candidates:
            return None

        return candidates[0]

    # ------------------------------------------------------------------
    # MediaPipe
    # ------------------------------------------------------------------

    def _initialize_mediapipe(self) -> None:
        """
        Initialize MediaPipe Hand Landmarker.
        """

        if mp is None:
            raise ImportError(
                "MediaPipe is not installed. "
                "Install it with: pip install mediapipe"
            )

        if self.mediapipe_model_path is None:
            raise FileNotFoundError(
                "MediaPipe model was not found.\n"
                "Expected a .task model inside:\n"
                f"{self.mediapipe_checkpoint_dir}"
            )

        if not self.mediapipe_model_path.exists():
            raise FileNotFoundError(
                f"MediaPipe model does not exist:\n"
                f"{self.mediapipe_model_path}"
            )

        try:
            BaseOptions = (
                mp.tasks.BaseOptions
            )

            HandLandmarker = (
                mp.tasks.vision.HandLandmarker
            )

            HandLandmarkerOptions = (
                mp.tasks.vision.HandLandmarkerOptions
            )

            VisionRunningMode = (
                mp.tasks.vision.RunningMode
            )

            options = HandLandmarkerOptions(
                base_options=BaseOptions(
                    model_asset_path=str(
                        self.mediapipe_model_path
                    )
                ),
                running_mode=VisionRunningMode.IMAGE,
                num_hands=self.max_num_hands,
                min_hand_detection_confidence=(
                    self.min_detection_confidence
                ),
                min_hand_presence_confidence=(
                    self.min_detection_confidence
                ),
                min_tracking_confidence=(
                    self.min_tracking_confidence
                ),
            )

            self.detector = HandLandmarker.create_from_options(
                options
            )

        except Exception as exc:
            raise RuntimeError(
                "Failed to initialize MediaPipe Hand Landmarker."
            ) from exc

    # ------------------------------------------------------------------
    # Image loading
    # ------------------------------------------------------------------

    def load_image(
        self,
        image: Union[str, Path, np.ndarray],
    ) -> np.ndarray:
        """
        Load image as RGB NumPy array.
        """

        if isinstance(image, (str, Path)):

            if cv2 is None:
                raise ImportError(
                    "OpenCV is required for image loading."
                )

            image_path = Path(image)

            if not image_path.exists():
                raise FileNotFoundError(
                    f"Image not found: {image_path}"
                )

            bgr = cv2.imread(str(image_path))

            if bgr is None:
                raise ValueError(
                    f"Unable to read image: {image_path}"
                )

            return cv2.cvtColor(
                bgr,
                cv2.COLOR_BGR2RGB,
            )

        array = np.asarray(image)

        if array.ndim != 3:
            raise ValueError(
                "Image must have shape (H, W, C)."
            )

        if array.shape[2] != 3:
            raise ValueError(
                "Image must contain 3 channels."
            )

        return array

    # ------------------------------------------------------------------
    # Detection
    # ------------------------------------------------------------------

    def detect(
        self,
        image: Union[str, Path, np.ndarray],
    ) -> List[HandDetection]:
        """
        Detect all hands in an image.
        """

        if self.detector is None:
            raise RuntimeError(
                "MediaPipe detector is not initialized."
            )

        rgb = self.load_image(image)

        if mp is None:
            raise ImportError(
                "MediaPipe is not installed."
            )

        mp_image = mp.Image(
            image_format=mp.ImageFormat.SRGB,
            data=rgb,
        )

        result = self.detector.detect(mp_image)

        detections: List[HandDetection] = []

        handedness_list = (
            result.handedness
            if hasattr(result, "handedness")
            else []
        )

        landmarks_list = (
            result.hand_landmarks
            if hasattr(result, "hand_landmarks")
            else []
        )

        world_landmarks_list = (
            result.hand_world_landmarks
            if hasattr(result, "hand_world_landmarks")
            else []
        )

        for index, landmarks in enumerate(
            landmarks_list
        ):

            coords = np.array(
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

            handedness = None
            handedness_score = None

            if (
                index < len(handedness_list)
                and handedness_list[index]
            ):
                category = handedness_list[index][0]

                handedness = category.category_name
                handedness_score = (
                    float(category.score)
                    if category.score is not None
                    else None
                )

            world_coords = None

            if (
                index < len(world_landmarks_list)
                and world_landmarks_list[index]
            ):
                world_coords = np.array(
                    [
                        [
                            landmark.x,
                            landmark.y,
                            landmark.z,
                        ]
                        for landmark
                        in world_landmarks_list[index]
                    ],
                    dtype=np.float32,
                )

            detections.append(
                HandDetection(
                    landmarks=coords,
                    handedness=handedness,
                    handedness_score=handedness_score,
                    world_landmarks=world_coords,
                    confidence=handedness_score,
                )
            )

        return detections

    # ------------------------------------------------------------------
    # Landmark normalization
    # ------------------------------------------------------------------

    def normalize_landmarks(
        self,
        landmarks: Union[
            np.ndarray,
            Sequence[Sequence[float]],
        ],
    ) -> np.ndarray:
        """
        Normalize landmarks relative to the wrist and hand scale.

        Steps:
            1. wrist becomes origin
            2. coordinates are centered
            3. scale is normalized using wrist -> middle MCP

        This makes the representation less dependent on:
            - image translation
            - hand size
        """

        points = _as_numpy(landmarks)

        _validate_landmarks(points)

        normalized = points.copy()

        wrist = normalized[WRIST].copy()

        normalized[:, :3] -= wrist[:3]

        scale = np.linalg.norm(
            normalized[MIDDLE_MCP, :3]
        )

        if scale < 1e-8:
            scale = 1.0

        normalized[:, :3] /= scale

        return normalized

    # ------------------------------------------------------------------
    # Palm measurements
    # ------------------------------------------------------------------

    def palm_width(
        self,
        landmarks: np.ndarray,
    ) -> float:
        """
        Approximate palm width.

        Uses:
            index MCP ↔ pinky MCP
        """

        return _distance(
            landmarks[INDEX_MCP, :3],
            landmarks[PINKY_MCP, :3],
        )

    def palm_length(
        self,
        landmarks: np.ndarray,
    ) -> float:
        """
        Approximate palm length.

        Uses:
            wrist ↔ middle MCP
        """

        return _distance(
            landmarks[WRIST, :3],
            landmarks[MIDDLE_MCP, :3],
        )

    # ------------------------------------------------------------------
    # Finger measurements
    # ------------------------------------------------------------------

    def finger_length(
        self,
        landmarks: np.ndarray,
        finger: str,
    ) -> float:
        """
        Calculate finger length.

        Supported:
            thumb
            index
            middle
            ring
            pinky
        """

        if finger not in FINGER_LANDMARKS:
            raise ValueError(
                f"Unknown finger: {finger}"
            )

        indices = FINGER_LANDMARKS[finger]

        total = 0.0

        for i in range(len(indices) - 1):

            total += _distance(
                landmarks[indices[i], :3],
                landmarks[indices[i + 1], :3],
            )

        return float(total)

    # ------------------------------------------------------------------
    # Finger angles
    # ------------------------------------------------------------------

    def finger_mcp_angle(
        self,
        landmarks: np.ndarray,
        finger: str,
    ) -> float:
        """
        Calculate MCP joint angle in degrees.
        """

        mapping = {
            "index": (
                WRIST,
                INDEX_MCP,
                INDEX_PIP,
            ),
            "middle": (
                WRIST,
                MIDDLE_MCP,
                MIDDLE_PIP,
            ),
            "ring": (
                WRIST,
                RING_MCP,
                RING_PIP,
            ),
            "pinky": (
                WRIST,
                PINKY_MCP,
                PINKY_PIP,
            ),
        }

        if finger not in mapping:
            raise ValueError(
                "MCP angle is only defined here "
                "for index, middle, ring and pinky."
            )

        a, b, c = mapping[finger]

        return _angle(
            landmarks[a, :3],
            landmarks[b, :3],
            landmarks[c, :3],
        )

    # ------------------------------------------------------------------
    # Hand area
    # ------------------------------------------------------------------

    def hand_area(
        self,
        landmarks: np.ndarray,
    ) -> float:
        """
        Approximate hand area using the convex hull
        of the main hand landmarks.

        Uses 2D x/y coordinates.
        """

        points = landmarks[
            [
                WRIST,
                THUMB_CMC,
                INDEX_MCP,
                MIDDLE_MCP,
                RING_MCP,
                PINKY_MCP,
                PINKY_TIP,
                RING_TIP,
                MIDDLE_TIP,
                INDEX_TIP,
                THUMB_TIP,
            ],
            :2,
        ]

        if cv2 is not None:

            hull = cv2.convexHull(
                points.astype(np.float32)
            )

            return float(
                cv2.contourArea(hull)
            )

        return _polygon_area(points)

    # ------------------------------------------------------------------
    # Fingertip spread
    # ------------------------------------------------------------------

    def fingertip_spread(
        self,
        landmarks: np.ndarray,
    ) -> float:
        """
        Mean distance between adjacent fingertips.
        """

        tips = np.array(
            [
                landmarks[THUMB_TIP, :3],
                landmarks[INDEX_TIP, :3],
                landmarks[MIDDLE_TIP, :3],
                landmarks[RING_TIP, :3],
                landmarks[PINKY_TIP, :3],
            ]
        )

        distances = []

        for i in range(len(tips) - 1):

            distances.append(
                _distance(
                    tips[i],
                    tips[i + 1],
                )
            )

        if not distances:
            return 0.0

        return float(
            np.mean(distances)
        )

    # ------------------------------------------------------------------
    # Feature extraction
    # ------------------------------------------------------------------

    def extract_features(
        self,
        detection: HandDetection,
        normalize: bool = True,
    ) -> HandFeatures:
        """
        Convert hand landmarks into a structured feature vector.
        """

        landmarks = detection.landmarks

        _validate_landmarks(landmarks)

        if normalize:

            normalized = self.normalize_landmarks(
                landmarks
            )

        else:

            normalized = landmarks.copy()

        palm_width = self.palm_width(
            normalized
        )

        palm_length = self.palm_length(
            normalized
        )

        finger_lengths = {
            finger: self.finger_length(
                normalized,
                finger,
            )
            for finger in FINGER_LANDMARKS
        }

        finger_angles = {
            finger: self.finger_mcp_angle(
                normalized,
                finger,
            )
            for finger in [
                "index",
                "middle",
                "ring",
                "pinky",
            ]
        }

        area = self.hand_area(
            normalized
        )

        if palm_length > 1e-8:

            aspect_ratio = (
                palm_width
                / palm_length
            )

        else:

            aspect_ratio = 0.0

        spread = self.fingertip_spread(
            normalized
        )

        return HandFeatures(
            handedness=detection.handedness,

            palm_width=palm_width,
            palm_length=palm_length,

            thumb_length=finger_lengths[
                "thumb"
            ],

            index_length=finger_lengths[
                "index"
            ],

            middle_length=finger_lengths[
                "middle"
            ],

            ring_length=finger_lengths[
                "ring"
            ],

            pinky_length=finger_lengths[
                "pinky"
            ],

            index_mcp_angle=finger_angles[
                "index"
            ],

            middle_mcp_angle=finger_angles[
                "middle"
            ],

            ring_mcp_angle=finger_angles[
                "ring"
            ],

            pinky_mcp_angle=finger_angles[
                "pinky"
            ],

            hand_area=area,
            hand_aspect_ratio=aspect_ratio,

            fingertip_spread=spread,

            normalized_landmarks=normalized,
            raw_landmarks=landmarks,
        )

    # ------------------------------------------------------------------
    # Feature vector
    # ------------------------------------------------------------------

    def features_to_vector(
        self,
        features: HandFeatures,
    ) -> np.ndarray:
        """
        Convert HandFeatures into a numerical vector.

        Useful for:
            - fusion models
            - regression
            - clustering
            - longitudinal modelling
        """

        scalar_features = np.array(
            [
                features.palm_width,
                features.palm_length,

                features.thumb_length,
                features.index_length,
                features.middle_length,
                features.ring_length,
                features.pinky_length,

                features.index_mcp_angle,
                features.middle_mcp_angle,
                features.ring_mcp_angle,
                features.pinky_mcp_angle,

                features.hand_area,
                features.hand_aspect_ratio,

                features.fingertip_spread,
            ],
            dtype=np.float32,
        )

        landmark_features = (
            features.normalized_landmarks[:, :3]
            .reshape(-1)
            .astype(np.float32)
        )

        return np.concatenate(
            [
                scalar_features,
                landmark_features,
            ]
        )

    # ------------------------------------------------------------------
    # Full image analysis
    # ------------------------------------------------------------------

    def analyze(
        self,
        image: Union[str, Path, np.ndarray],
    ) -> List[Dict[str, Any]]:
        """
        Detect and analyze all hands in an image.

        Returns:
            list of dictionaries
        """

        detections = self.detect(image)

        results = []

        for detection in detections:

            features = self.extract_features(
                detection
            )

            vector = self.features_to_vector(
                features
            )

            results.append(
                {
                    "handedness": (
                        detection.handedness
                    ),
                    "confidence": (
                        detection.confidence
                    ),
                    "landmarks": (
                        detection.landmarks
                    ),
                    "world_landmarks": (
                        detection.world_landmarks
                    ),
                    "features": features,
                    "feature_vector": vector,
                }
            )

        return results

    # ------------------------------------------------------------------
    # Batch analysis
    # ------------------------------------------------------------------

    def analyze_batch(
        self,
        images: Sequence[
            Union[str, Path, np.ndarray]
        ],
    ) -> List[List[Dict[str, Any]]]:
        """
        Analyze multiple images.
        """

        outputs = []

        for image in images:

            outputs.append(
                self.analyze(image)
            )

        return outputs

    # ------------------------------------------------------------------
    # Serialization
    # ------------------------------------------------------------------

    @staticmethod
    def features_to_dict(
        features: HandFeatures,
    ) -> Dict[str, Any]:
        """
        Convert HandFeatures into a JSON-compatible dictionary.
        """

        return {
            "handedness": features.handedness,

            "palm_width": (
                features.palm_width
            ),

            "palm_length": (
                features.palm_length
            ),

            "thumb_length": (
                features.thumb_length
            ),

            "index_length": (
                features.index_length
            ),

            "middle_length": (
                features.middle_length
            ),

            "ring_length": (
                features.ring_length
            ),

            "pinky_length": (
                features.pinky_length
            ),

            "index_mcp_angle": (
                features.index_mcp_angle
            ),

            "middle_mcp_angle": (
                features.middle_mcp_angle
            ),

            "ring_mcp_angle": (
                features.ring_mcp_angle
            ),

            "pinky_mcp_angle": (
                features.pinky_mcp_angle
            ),

            "hand_area": (
                features.hand_area
            ),

            "hand_aspect_ratio": (
                features.hand_aspect_ratio
            ),

            "fingertip_spread": (
                features.fingertip_spread
            ),

            "normalized_landmarks": (
                features.normalized_landmarks.tolist()
            ),

            "raw_landmarks": (
                features.raw_landmarks.tolist()
            ),
        }

    # ------------------------------------------------------------------
    # Model information
    # ------------------------------------------------------------------

    def info(self) -> Dict[str, Any]:
        """
        Return model configuration.
        """

        return {
            "model": "HandModel",
            "device": self.device,
            "max_num_hands": (
                self.max_num_hands
            ),
            "mediapipe_model": (
                str(self.mediapipe_model_path)
                if self.mediapipe_model_path
                else None
            ),
            "mano_checkpoint_dir": (
                str(self.mano_checkpoint_dir)
            ),
            "landmarks": NUM_HAND_LANDMARKS,
        }


# ---------------------------------------------------------------------------
# Convenience function
# ---------------------------------------------------------------------------

def create_hand_model(
    checkpoint_dir: Optional[
        Union[str, Path]
    ] = None,
    **kwargs: Any,
) -> HandModel:
    """
    Factory function for creating HandModel.
    """

    return HandModel(
        checkpoint_dir=checkpoint_dir,
        **kwargs,
    )


# ---------------------------------------------------------------------------
# Example
# ---------------------------------------------------------------------------

if __name__ == "__main__":

    import argparse

    parser = argparse.ArgumentParser(
        description="Analyze hand landmarks."
    )

    parser.add_argument(
        "--image",
        type=str,
        required=True,
        help="Path to input image.",
    )

    parser.add_argument(
        "--checkpoint-dir",
        type=str,
        default=None,
        help="Checkpoint directory.",
    )

    args = parser.parse_args()

    model = create_hand_model(
        checkpoint_dir=args.checkpoint_dir
    )

    print("\nModel:")
    print(model.info())

    results = model.analyze(
        args.image
    )

    print(
        f"\nDetected hands: {len(results)}"
    )

    for i, result in enumerate(results):

        print(
            f"\nHand {i + 1}"
        )

        print(
            f"  handedness: "
            f"{result['handedness']}"
        )

        print(
            f"  confidence: "
            f"{result['confidence']}"
        )

        features = result["features"]

        print(
            f"  palm width: "
            f"{features.palm_width:.4f}"
        )

        print(
            f"  palm length: "
            f"{features.palm_length:.4f}"
        )

        print(
            f"  index length: "
            f"{features.index_length:.4f}"
        )

        print(
            f"  middle length: "
            f"{features.middle_length:.4f}"
        )

        print(
            f"  ring length: "
            f"{features.ring_length:.4f}"
        )

        print(
            f"  pinky length: "
            f"{features.pinky_length:.4f}"
        )