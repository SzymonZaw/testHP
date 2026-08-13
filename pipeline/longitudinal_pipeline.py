# longitudinal_pipeline.py
"""
Longitudinal Pipeline
=====================

Pipeline for processing longitudinal patient data.

Expected structure:

data/
└── longitudinal/
    ├── T0/
    ├── T1/
    ├── T2/
    └── T3/

Each timepoint may contain multimodal data, for example:

T0/
├── images/
├── rna/
├── hand/
├── cells/
└── metadata.json

T1/
├── images/
├── rna/
├── hand/
├── cells/
└── metadata.json

The pipeline is responsible for:

1. discovering timepoints,
2. loading patient/timepoint metadata,
3. identifying available modalities,
4. connecting observations belonging to the same patient,
5. creating a chronological representation,
6. extracting features from supplied models/pipelines,
7. calculating temporal changes,
8. preparing data for longitudinal_model.py,
9. preparing state updates for digital_twin.py.

The pipeline DOES NOT itself decide:
- whether a patient is healthy,
- whether a lesion is malignant,
- what treatment should be used,
- what intervention should be recommended.

Those responsibilities belong to:
    models/
    analysis/
    decision/
    digital_twin/
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Union

import numpy as np
import torch


# ---------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------
# Type aliases
# ---------------------------------------------------------------------

PathLike = Union[str, Path]


# ---------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------

DEFAULT_TIMEPOINTS = (
    "T0",
    "T1",
    "T2",
    "T3",
)

DEFAULT_MODALITIES = (
    "images",
    "rna",
    "hand",
    "cells",
)


# ---------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------

@dataclass
class LongitudinalPipelineConfig:
    """
    Configuration of the longitudinal pipeline.
    """

    longitudinal_dir: PathLike = "data/longitudinal"

    timepoints: Sequence[str] = DEFAULT_TIMEPOINTS

    modalities: Sequence[str] = DEFAULT_MODALITIES

    output_dir: PathLike = "data/processed"

    save_features: bool = True
    save_metadata: bool = True
    save_temporal_data: bool = True

    normalize_features: bool = False

    device: Optional[str] = None


# ---------------------------------------------------------------------
# Timepoint data
# ---------------------------------------------------------------------

@dataclass
class TimepointRecord:
    """
    Information about one longitudinal timepoint.
    """

    timepoint: str

    path: str

    exists: bool

    modalities: Dict[str, List[str]] = field(
        default_factory=dict
    )

    metadata: Dict[str, Any] = field(
        default_factory=dict
    )


# ---------------------------------------------------------------------
# Patient longitudinal record
# ---------------------------------------------------------------------

@dataclass
class LongitudinalRecord:
    """
    Complete longitudinal record for one patient.
    """

    patient_id: str

    timepoints: List[TimepointRecord]

    available_timepoints: List[str]

    missing_timepoints: List[str]

    modality_history: Dict[str, List[str]]

    features: Dict[str, Any] = field(
        default_factory=dict
    )

    temporal_changes: Dict[str, Any] = field(
        default_factory=dict
    )


# ---------------------------------------------------------------------
# Utility functions
# ---------------------------------------------------------------------

def _ensure_directory(path: PathLike) -> Path:
    """
    Create directory if it does not exist.
    """

    path = Path(path)

    path.mkdir(
        parents=True,
        exist_ok=True,
    )

    return path


def _to_numpy(value: Any) -> Optional[np.ndarray]:
    """
    Convert common tensor-like objects to numpy.
    """

    if value is None:
        return None

    if isinstance(value, np.ndarray):
        return value

    if torch.is_tensor(value):
        return value.detach().cpu().numpy()

    if isinstance(value, list):
        try:
            return np.asarray(value)
        except Exception:
            return None

    if isinstance(value, tuple):
        try:
            return np.asarray(value)
        except Exception:
            return None

    return None


def _safe_float(value: Any) -> Optional[float]:
    """
    Convert scalar-like value to float.
    """

    try:
        return float(value)
    except Exception:
        return None


# ---------------------------------------------------------------------
# Main pipeline
# ---------------------------------------------------------------------

class LongitudinalPipeline:
    """
    Main longitudinal processing pipeline.

    It organizes observations across T0/T1/T2/T3 and prepares
    temporal features for downstream models.
    """

    def __init__(
        self,
        config: Optional[LongitudinalPipelineConfig] = None,
        image_pipeline: Optional[Any] = None,
        rna_pipeline: Optional[Any] = None,
        hand_pipeline: Optional[Any] = None,
        cell_pipeline: Optional[Any] = None,
        longitudinal_model: Optional[Any] = None,
        digital_twin: Optional[Any] = None,
    ):
        self.config = (
            config
            or LongitudinalPipelineConfig()
        )

        self.image_pipeline = image_pipeline
        self.rna_pipeline = rna_pipeline
        self.hand_pipeline = hand_pipeline
        self.cell_pipeline = cell_pipeline

        self.longitudinal_model = longitudinal_model
        self.digital_twin = digital_twin

        self.longitudinal_dir = Path(
            self.config.longitudinal_dir
        )

        self.output_dir = _ensure_directory(
            self.config.output_dir
        )

        self.temporal_output_dir = _ensure_directory(
            self.output_dir / "longitudinal"
        )

        self.device = self._resolve_device()

        logger.info(
            "LongitudinalPipeline initialized."
        )

    # -----------------------------------------------------------------
    # Device
    # -----------------------------------------------------------------

    def _resolve_device(self) -> torch.device:
        """
        Select computation device.
        """

        if self.config.device:
            return torch.device(
                self.config.device
            )

        if torch.cuda.is_available():
            return torch.device("cuda")

        return torch.device("cpu")

    # -----------------------------------------------------------------
    # Timepoint discovery
    # -----------------------------------------------------------------

    def discover_timepoints(self) -> List[str]:
        """
        Discover available T0/T1/T2/T3 directories.
        """

        available = []

        for timepoint in self.config.timepoints:

            path = (
                self.longitudinal_dir
                / timepoint
            )

            if path.exists() and path.is_dir():
                available.append(timepoint)

        return available

    # -----------------------------------------------------------------
    # Patient discovery
    # -----------------------------------------------------------------

    def discover_patients(
        self,
        timepoint: str,
    ) -> List[str]:
        """
        Discover patient IDs inside a timepoint.

        Expected structure:

        T0/
            patient_001/
            patient_002/
            ...

        If the directory contains files directly rather than patient
        directories, the method returns an empty list.
        """

        timepoint_dir = (
            self.longitudinal_dir
            / timepoint
        )

        if not timepoint_dir.exists():
            return []

        patients = []

        for path in timepoint_dir.iterdir():

            if path.is_dir():
                patients.append(
                    path.name
                )

        return sorted(patients)

    # -----------------------------------------------------------------
    # All patient discovery
    # -----------------------------------------------------------------

    def discover_all_patients(self) -> List[str]:
        """
        Find patient IDs across all timepoints.
        """

        patient_ids = set()

        for timepoint in self.config.timepoints:

            patients = self.discover_patients(
                timepoint
            )

            patient_ids.update(
                patients
            )

        return sorted(patient_ids)

    # -----------------------------------------------------------------
    # Modality discovery
    # -----------------------------------------------------------------

    def discover_modalities(
        self,
        patient_dir: Path,
    ) -> Dict[str, List[str]]:
        """
        Identify files available for each modality.
        """

        result: Dict[str, List[str]] = {}

        for modality in self.config.modalities:

            modality_dir = (
                patient_dir / modality
            )

            if not modality_dir.exists():
                result[modality] = []
                continue

            files = []

            for path in modality_dir.rglob("*"):

                if path.is_file():

                    files.append(
                        str(path)
                    )

            result[modality] = sorted(
                files
            )

        return result

    # -----------------------------------------------------------------
    # Metadata loading
    # -----------------------------------------------------------------

    def load_metadata(
        self,
        patient_dir: Path,
    ) -> Dict[str, Any]:
        """
        Load patient metadata.

        Supported file:

            metadata.json
        """

        metadata_path = (
            patient_dir / "metadata.json"
        )

        if not metadata_path.exists():
            return {}

        try:

            with open(
                metadata_path,
                "r",
                encoding="utf-8",
            ) as file:

                data = json.load(file)

            if isinstance(data, dict):
                return data

        except Exception as exc:

            logger.warning(
                "Could not load metadata from %s: %s",
                metadata_path,
                exc,
            )

        return {}

    # -----------------------------------------------------------------
    # Build timepoint record
    # -----------------------------------------------------------------

    def build_timepoint_record(
        self,
        patient_id: str,
        timepoint: str,
    ) -> TimepointRecord:
        """
        Build a record describing one patient's timepoint.
        """

        patient_dir = (
            self.longitudinal_dir
            / timepoint
            / patient_id
        )

        exists = (
            patient_dir.exists()
            and patient_dir.is_dir()
        )

        if not exists:

            return TimepointRecord(
                timepoint=timepoint,
                path=str(patient_dir),
                exists=False,
                modalities={},
                metadata={},
            )

        modalities = self.discover_modalities(
            patient_dir
        )

        metadata = self.load_metadata(
            patient_dir
        )

        return TimepointRecord(
            timepoint=timepoint,
            path=str(patient_dir),
            exists=True,
            modalities=modalities,
            metadata=metadata,
        )

    # -----------------------------------------------------------------
    # Build patient record
    # -----------------------------------------------------------------

    def build_patient_record(
        self,
        patient_id: str,
    ) -> LongitudinalRecord:
        """
        Build complete longitudinal record for one patient.
        """

        records = []

        available = []

        missing = []

        modality_history: Dict[
            str,
            List[str]
        ] = {
            modality: []
            for modality in self.config.modalities
        }

        for timepoint in self.config.timepoints:

            record = self.build_timepoint_record(
                patient_id,
                timepoint,
            )

            records.append(record)

            if record.exists:

                available.append(
                    timepoint
                )

                for modality in self.config.modalities:

                    if record.modalities.get(
                        modality
                    ):
                        modality_history[
                            modality
                        ].append(timepoint)

            else:

                missing.append(
                    timepoint
                )

        return LongitudinalRecord(
            patient_id=patient_id,
            timepoints=records,
            available_timepoints=available,
            missing_timepoints=missing,
            modality_history=modality_history,
        )

    # -----------------------------------------------------------------
    # Feature extraction
    # -----------------------------------------------------------------

    def extract_features(
        self,
        patient_record: LongitudinalRecord,
    ) -> Dict[str, Any]:
        """
        Extract optional features using supplied modality pipelines.

        The method is intentionally defensive: if a particular
        pipeline is unavailable, the longitudinal record can still
        be constructed.
        """

        features: Dict[str, Any] = {}

        for timepoint_record in (
            patient_record.timepoints
        ):

            if not timepoint_record.exists:
                continue

            timepoint = (
                timepoint_record.timepoint
            )

            features[timepoint] = {}

            # ---------------------------------------------------------
            # Images
            # ---------------------------------------------------------

            image_files = (
                timepoint_record.modalities
                .get("images", [])
            )

            if (
                image_files
                and self.image_pipeline is not None
            ):

                image_features = []

                for image_path in image_files:

                    try:

                        result = (
                            self.image_pipeline.process(
                                image_path
                            )
                        )

                        embedding = getattr(
                            result,
                            "embedding_shape",
                            None,
                        )

                        image_features.append(
                            {
                                "path": image_path,
                                "embedding_shape": (
                                    list(embedding)
                                    if embedding
                                    else None
                                ),
                            }
                        )

                    except Exception as exc:

                        logger.warning(
                            "Image processing failed "
                            "for %s: %s",
                            image_path,
                            exc,
                        )

                features[timepoint][
                    "images"
                ] = image_features

            # ---------------------------------------------------------
            # RNA
            # ---------------------------------------------------------

            rna_files = (
                timepoint_record.modalities
                .get("rna", [])
            )

            if (
                rna_files
                and self.rna_pipeline is not None
            ):

                rna_features = []

                for rna_path in rna_files:

                    try:

                        if hasattr(
                            self.rna_pipeline,
                            "process",
                        ):

                            result = (
                                self.rna_pipeline.process(
                                    rna_path
                                )
                            )

                        elif callable(
                            self.rna_pipeline
                        ):

                            result = (
                                self.rna_pipeline(
                                    rna_path
                                )
                            )

                        else:

                            result = None

                        rna_features.append(
                            {
                                "path": rna_path,
                                "result": result,
                            }
                        )

                    except Exception as exc:

                        logger.warning(
                            "RNA processing failed "
                            "for %s: %s",
                            rna_path,
                            exc,
                        )

                features[timepoint][
                    "rna"
                ] = rna_features

            # ---------------------------------------------------------
            # Hand
            # ---------------------------------------------------------

            hand_files = (
                timepoint_record.modalities
                .get("hand", [])
            )

            if (
                hand_files
                and self.hand_pipeline is not None
            ):

                hand_features = []

                for hand_path in hand_files:

                    try:

                        if hasattr(
                            self.hand_pipeline,
                            "process",
                        ):

                            result = (
                                self.hand_pipeline.process(
                                    hand_path
                                )
                            )

                        elif callable(
                            self.hand_pipeline
                        ):

                            result = (
                                self.hand_pipeline(
                                    hand_path
                                )
                            )

                        else:

                            result = None

                        hand_features.append(
                            {
                                "path": hand_path,
                                "result": result,
                            }
                        )

                    except Exception as exc:

                        logger.warning(
                            "Hand processing failed "
                            "for %s: %s",
                            hand_path,
                            exc,
                        )

                features[timepoint][
                    "hand"
                ] = hand_features

            # ---------------------------------------------------------
            # Cells
            # ---------------------------------------------------------

            cell_files = (
                timepoint_record.modalities
                .get("cells", [])
            )

            if (
                cell_files
                and self.cell_pipeline is not None
            ):

                cell_features = []

                for cell_path in cell_files:

                    try:

                        if hasattr(
                            self.cell_pipeline,
                            "process",
                        ):

                            result = (
                                self.cell_pipeline.process(
                                    cell_path
                                )
                            )

                        elif callable(
                            self.cell_pipeline
                        ):

                            result = (
                                self.cell_pipeline(
                                    cell_path
                                )
                            )

                        else:

                            result = None

                        cell_features.append(
                            {
                                "path": cell_path,
                                "result": result,
                            }
                        )

                    except Exception as exc:

                        logger.warning(
                            "Cell processing failed "
                            "for %s: %s",
                            cell_path,
                            exc,
                        )

                features[timepoint][
                    "cells"
                ] = cell_features

        return features

    # -----------------------------------------------------------------
    # Numerical temporal change
    # -----------------------------------------------------------------

    def calculate_change(
        self,
        initial: Any,
        final: Any,
    ) -> Optional[Any]:
        """
        Calculate absolute change between two numerical feature
        representations.

        Supports:
            scalar
            numpy array
            torch tensor
            list
        """

        initial_array = _to_numpy(
            initial
        )

        final_array = _to_numpy(
            final
        )

        if (
            initial_array is None
            or final_array is None
        ):
            return None

        if initial_array.shape != final_array.shape:
            return None

        return final_array - initial_array

    # -----------------------------------------------------------------
    # Percentage change
    # -----------------------------------------------------------------

    def calculate_percentage_change(
        self,
        initial: Any,
        final: Any,
        epsilon: float = 1e-8,
    ) -> Optional[Any]:
        """
        Calculate percentage change.
        """

        initial_array = _to_numpy(
            initial
        )

        final_array = _to_numpy(
            final
        )

        if (
            initial_array is None
            or final_array is None
        ):
            return None

        if initial_array.shape != final_array.shape:
            return None

        return (
            (final_array - initial_array)
            / (np.abs(initial_array) + epsilon)
        ) * 100.0

    # -----------------------------------------------------------------
    # Generic temporal comparison
    # -----------------------------------------------------------------

    def compare_timepoints(
        self,
        values: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Compare chronological values.

        Example:

            {
                "T0": 0.2,
                "T1": 0.3,
                "T2": 0.5
            }

        returns changes between consecutive timepoints.
        """

        result: Dict[str, Any] = {}

        ordered = [
            timepoint
            for timepoint in self.config.timepoints
            if timepoint in values
        ]

        for index in range(
            1,
            len(ordered),
        ):

            previous = ordered[index - 1]
            current = ordered[index]

            change = self.calculate_change(
                values[previous],
                values[current],
            )

            percentage = (
                self.calculate_percentage_change(
                    values[previous],
                    values[current],
                )
            )

            result[
                f"{previous}_to_{current}"
            ] = {
                "absolute_change": (
                    change.tolist()
                    if isinstance(
                        change,
                        np.ndarray,
                    )
                    else change
                ),
                "percentage_change": (
                    percentage.tolist()
                    if isinstance(
                        percentage,
                        np.ndarray,
                    )
                    else percentage
                ),
            }

        return result

    # -----------------------------------------------------------------
    # Build temporal summary
    # -----------------------------------------------------------------

    def build_temporal_summary(
        self,
        patient_record: LongitudinalRecord,
    ) -> Dict[str, Any]:
        """
        Create high-level temporal summary.

        This is descriptive and does not represent a clinical
        interpretation.
        """

        summary: Dict[str, Any] = {
            "patient_id": patient_record.patient_id,
            "available_timepoints": (
                patient_record.available_timepoints
            ),
            "missing_timepoints": (
                patient_record.missing_timepoints
            ),
            "num_timepoints": len(
                patient_record.available_timepoints
            ),
            "modality_history": (
                patient_record.modality_history
            ),
        }

        # -------------------------------------------------------------
        # Time coverage
        # -------------------------------------------------------------

        summary["longitudinal_coverage"] = (
            len(
                patient_record.available_timepoints
            )
            / max(
                len(self.config.timepoints),
                1,
            )
        )

        # -------------------------------------------------------------
        # Consecutive observations
        # -------------------------------------------------------------

        available = (
            patient_record.available_timepoints
        )

        consecutive_pairs = []

        for index in range(
            1,
            len(available),
        ):

            consecutive_pairs.append(
                [
                    available[index - 1],
                    available[index],
                ]
            )

        summary["consecutive_pairs"] = (
            consecutive_pairs
        )

        return summary

    # -----------------------------------------------------------------
    # Prepare model input
    # -----------------------------------------------------------------

    def prepare_model_input(
        self,
        patient_record: LongitudinalRecord,
    ) -> Dict[str, Any]:
        """
        Prepare a structured input for longitudinal_model.py.

        The model receives a chronological sequence instead of raw
        files.
        """

        sequence = []

        for timepoint in (
            patient_record.timepoints
        ):

            if not timepoint.exists:
                continue

            sequence.append(
                {
                    "timepoint": (
                        timepoint.timepoint
                    ),
                    "modalities": (
                        timepoint.modalities
                    ),
                    "metadata": (
                        timepoint.metadata
                    ),
                }
            )

        return {
            "patient_id": (
                patient_record.patient_id
            ),
            "sequence": sequence,
        }

    # -----------------------------------------------------------------
    # Longitudinal model
    # -----------------------------------------------------------------

    def run_longitudinal_model(
        self,
        model_input: Dict[str, Any],
    ) -> Optional[Any]:
        """
        Run supplied longitudinal model.
        """

        if self.longitudinal_model is None:
            return None

        model = self.longitudinal_model

        try:

            if hasattr(
                model,
                "predict",
            ):

                return model.predict(
                    model_input
                )

            if hasattr(
                model,
                "forward",
            ):

                return model.forward(
                    model_input
                )

            if callable(model):

                return model(
                    model_input
                )

        except Exception as exc:

            logger.exception(
                "Longitudinal model failed: %s",
                exc,
            )

        return None

    # -----------------------------------------------------------------
    # Digital twin update
    # -----------------------------------------------------------------

    def update_digital_twin(
        self,
        patient_record: LongitudinalRecord,
        model_output: Optional[Any] = None,
    ) -> Optional[Any]:
        """
        Pass longitudinal information to the digital twin.

        The exact API is intentionally flexible.
        """

        if self.digital_twin is None:
            return None

        twin = self.digital_twin

        payload = {
            "patient_id": (
                patient_record.patient_id
            ),
            "timepoints": [
                asdict(record)
                for record in patient_record.timepoints
            ],
            "model_output": model_output,
        }

        try:

            if hasattr(
                twin,
                "update",
            ):

                return twin.update(
                    payload
                )

            if hasattr(
                twin,
                "update_state",
            ):

                return twin.update_state(
                    payload
                )

            if callable(twin):

                return twin(
                    payload
                )

        except Exception as exc:

            logger.exception(
                "Digital twin update failed: %s",
                exc,
            )

        return None

    # -----------------------------------------------------------------
    # Save patient record
    # -----------------------------------------------------------------

    def save_patient_record(
        self,
        patient_record: LongitudinalRecord,
    ) -> Path:
        """
        Save longitudinal record as JSON.
        """

        patient_dir = _ensure_directory(
            self.temporal_output_dir
            / patient_record.patient_id
        )

        output_path = (
            patient_dir
            / "longitudinal_record.json"
        )

        with open(
            output_path,
            "w",
            encoding="utf-8",
        ) as file:

            json.dump(
                asdict(patient_record),
                file,
                indent=2,
                ensure_ascii=False,
                default=str,
            )

        return output_path

    # -----------------------------------------------------------------
    # Save temporal summary
    # -----------------------------------------------------------------

    def save_temporal_summary(
        self,
        patient_id: str,
        summary: Dict[str, Any],
    ) -> Path:
        """
        Save temporal summary.
        """

        patient_dir = _ensure_directory(
            self.temporal_output_dir
            / patient_id
        )

        output_path = (
            patient_dir
            / "temporal_summary.json"
        )

        with open(
            output_path,
            "w",
            encoding="utf-8",
        ) as file:

            json.dump(
                summary,
                file,
                indent=2,
                ensure_ascii=False,
                default=str,
            )

        return output_path

    # -----------------------------------------------------------------
    # Process one patient
    # -----------------------------------------------------------------

    def process_patient(
        self,
        patient_id: str,
    ) -> Dict[str, Any]:
        """
        Complete processing of one patient.
        """

        logger.info(
            "Processing longitudinal patient: %s",
            patient_id,
        )

        # -------------------------------------------------------------
        # Build longitudinal structure
        # -------------------------------------------------------------

        patient_record = (
            self.build_patient_record(
                patient_id
            )
        )

        # -------------------------------------------------------------
        # Extract modality features
        # -------------------------------------------------------------

        try:

            features = self.extract_features(
                patient_record
            )

            patient_record.features = (
                features
            )

        except Exception as exc:

            logger.exception(
                "Feature extraction failed for %s: %s",
                patient_id,
                exc,
            )

        # -------------------------------------------------------------
        # Temporal summary
        # -------------------------------------------------------------

        temporal_summary = (
            self.build_temporal_summary(
                patient_record
            )
        )

        # -------------------------------------------------------------
        # Model input
        # -------------------------------------------------------------

        model_input = (
            self.prepare_model_input(
                patient_record
            )
        )

        # -------------------------------------------------------------
        # Longitudinal model
        # -------------------------------------------------------------

        model_output = (
            self.run_longitudinal_model(
                model_input
            )
        )

        # -------------------------------------------------------------
        # Digital twin
        # -------------------------------------------------------------

        twin_output = (
            self.update_digital_twin(
                patient_record,
                model_output=model_output,
            )
        )

        # -------------------------------------------------------------
        # Save
        # -------------------------------------------------------------

        record_path = None
        summary_path = None

        if self.config.save_temporal_data:

            record_path = str(
                self.save_patient_record(
                    patient_record
                )
            )

            summary_path = str(
                self.save_temporal_summary(
                    patient_id,
                    temporal_summary,
                )
            )

        # -------------------------------------------------------------
        # Return
        # -------------------------------------------------------------

        return {
            "patient_id": patient_id,
            "record": patient_record,
            "temporal_summary": temporal_summary,
            "model_input": model_input,
            "model_output": model_output,
            "digital_twin_output": twin_output,
            "record_path": record_path,
            "summary_path": summary_path,
        }

    # -----------------------------------------------------------------
    # Process all patients
    # -----------------------------------------------------------------

    def process_all_patients(
        self,
    ) -> Dict[str, Dict[str, Any]]:
        """
        Process every patient found across T0-T3.
        """

        patient_ids = (
            self.discover_all_patients()
        )

        logger.info(
            "Found %d longitudinal patients.",
            len(patient_ids),
        )

        results = {}

        for patient_id in patient_ids:

            try:

                results[patient_id] = (
                    self.process_patient(
                        patient_id
                    )
                )

            except Exception as exc:

                logger.exception(
                    "Longitudinal processing failed "
                    "for patient %s: %s",
                    patient_id,
                    exc,
                )

        return results


# ---------------------------------------------------------------------
# Convenience function
# ---------------------------------------------------------------------

def process_patient_longitudinal(
    patient_id: str,
    config: Optional[
        LongitudinalPipelineConfig
    ] = None,
    image_pipeline: Optional[Any] = None,
    rna_pipeline: Optional[Any] = None,
    hand_pipeline: Optional[Any] = None,
    cell_pipeline: Optional[Any] = None,
    longitudinal_model: Optional[Any] = None,
    digital_twin: Optional[Any] = None,
) -> Dict[str, Any]:
    """
    Convenience function for one patient.
    """

    pipeline = LongitudinalPipeline(
        config=config,
        image_pipeline=image_pipeline,
        rna_pipeline=rna_pipeline,
        hand_pipeline=hand_pipeline,
        cell_pipeline=cell_pipeline,
        longitudinal_model=longitudinal_model,
        digital_twin=digital_twin,
    )

    return pipeline.process_patient(
        patient_id
    )


# ---------------------------------------------------------------------
# Demo
# ---------------------------------------------------------------------

def _demo() -> None:
    """
    Basic smoke test.

    Creates a temporary-like demonstration structure inside
    data/longitudinal if it already exists.

    No ML model is required.
    """

    logging.basicConfig(
        level=logging.INFO,
        format="%(levelname)s | %(message)s",
    )

    print()
    print("=" * 70)
    print("Longitudinal Pipeline")
    print("=" * 70)

    config = LongitudinalPipelineConfig(
        longitudinal_dir="data/longitudinal",
        timepoints=(
            "T0",
            "T1",
            "T2",
            "T3",
        ),
    )

    pipeline = LongitudinalPipeline(
        config=config
    )

    available_timepoints = (
        pipeline.discover_timepoints()
    )

    print()
    print(
        "Available timepoints:",
        available_timepoints,
    )

    patients = (
        pipeline.discover_all_patients()
    )

    print(
        "Discovered patients:",
        patients,
    )

    # If no real patients exist yet, demonstrate
    # the data structure using a synthetic ID.
    patient_id = (
        patients[0]
        if patients
        else "demo_patient"
    )

    result = pipeline.process_patient(
        patient_id
    )

    print()
    print(
        "Patient:",
        result["patient_id"],
    )

    print(
        "Available:",
        result[
            "temporal_summary"
        ]["available_timepoints"],
    )

    print(
        "Missing:",
        result[
            "temporal_summary"
        ]["missing_timepoints"],
    )

    print(
        "Longitudinal coverage:",
        result[
            "temporal_summary"
        ]["longitudinal_coverage"],
    )

    print()
    print(
        "Longitudinal pipeline ready."
    )


# ---------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------

if __name__ == "__main__":
    _demo()