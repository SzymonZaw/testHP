from __future__ import annotations

from dataclasses import dataclass
from math import hypot
from typing import Iterable

from .spatial_registration_contract import (
    RegistrationAssessment,
    RegistrationStatus,
    SpatialTransform,
)


@dataclass(frozen=True)
class LandmarkPair:
    """One correspondence between sample-local and canonical hand space."""

    landmark_id: str
    source_xy: tuple[float, float]
    target_xy: tuple[float, float]
    evidence_id: str | None = None


@dataclass(frozen=True)
class LandmarkRegistrationConfig:
    min_landmarks: int = 3
    max_rms_error: float = 5.0
    source_frame: str = "sample_local"
    target_frame: str = "canonical_hand_2d"
    model_version: str = "affine-2d-v1"


def _solve_3x3(a: list[list[float]], b: list[float]) -> list[float]:
    m = [row[:] + [rhs] for row, rhs in zip(a, b)]
    for col in range(3):
        pivot = max(range(col, 3), key=lambda r: abs(m[r][col]))
        if abs(m[pivot][col]) < 1e-12:
            raise ValueError("landmarks are degenerate or collinear")
        m[col], m[pivot] = m[pivot], m[col]
        scale = m[col][col]
        m[col] = [v / scale for v in m[col]]
        for row in range(3):
            if row == col:
                continue
            factor = m[row][col]
            m[row] = [m[row][j] - factor * m[col][j] for j in range(4)]
    return [m[i][3] for i in range(3)]


def _fit_affine(pairs: list[LandmarkPair]) -> tuple[tuple[float, float, float], ...]:
    # Solve the two affine output coordinates independently using normal equations.
    ata = [[0.0] * 3 for _ in range(3)]
    atx = [0.0] * 3
    aty = [0.0] * 3
    for pair in pairs:
        x, y = pair.source_xy
        X, Y = pair.target_xy
        row = (x, y, 1.0)
        for i in range(3):
            for j in range(3):
                ata[i][j] += row[i] * row[j]
            atx[i] += row[i] * X
            aty[i] += row[i] * Y
    ax = _solve_3x3(ata, atx)
    ay = _solve_3x3(ata, aty)
    return (
        (ax[0], ax[1], ax[2]),
        (ay[0], ay[1], ay[2]),
        (0.0, 0.0, 1.0),
    )


def _apply(matrix: tuple[tuple[float, float, float], ...], xy: tuple[float, float]) -> tuple[float, float]:
    x, y = xy
    return (
        matrix[0][0] * x + matrix[0][1] * y + matrix[0][2],
        matrix[1][0] * x + matrix[1][1] * y + matrix[1][2],
    )


def assess_landmark_registration(
    source_id: str,
    source_region: str,
    target_region: str,
    landmarks: Iterable[LandmarkPair],
    *,
    anatomical_match: bool = False,
    config: LandmarkRegistrationConfig | None = None,
) -> RegistrationAssessment:
    """Fit an affine candidate without ever implying registration is verified.

    Verification requires explicit anatomical confirmation and evidence IDs.
    RMS error is a quality gate for the candidate; it is not, by itself,
    evidence that two biological samples are anatomically identical.
    """
    cfg = config or LandmarkRegistrationConfig()
    pairs = list(landmarks)
    if len(pairs) < cfg.min_landmarks:
        return RegistrationAssessment(
            source_id=source_id,
            source_region=source_region,
            target_region=target_region,
            status=RegistrationStatus.UNREGISTERED,
            anatomical_match=anatomical_match,
            limitations=(f"at least {cfg.min_landmarks} non-collinear landmarks are required",),
        )

    evidence_ids = tuple(dict.fromkeys(p.evidence_id for p in pairs if p.evidence_id))
    try:
        matrix = _fit_affine(pairs)
    except ValueError as exc:
        return RegistrationAssessment(
            source_id=source_id,
            source_region=source_region,
            target_region=target_region,
            status=RegistrationStatus.UNREGISTERED,
            anatomical_match=anatomical_match,
            limitations=(str(exc),),
        )

    errors = []
    for pair in pairs:
        predicted = _apply(matrix, pair.source_xy)
        errors.append(hypot(predicted[0] - pair.target_xy[0], predicted[1] - pair.target_xy[1]))
    rms = (sum(error * error for error in errors) / len(errors)) ** 0.5

    transform = SpatialTransform(
        transform_id=f"landmark-affine:{source_id}:{source_region}:{target_region}",
        source_frame=cfg.source_frame,
        target_frame=cfg.target_frame,
        matrix=matrix,
        method="landmark_affine_2d",
        status=RegistrationStatus.CANDIDATE,
        evidence_ids=evidence_ids,
        model_version=cfg.model_version,
    )
    limitations = (f"landmark_rms_error={rms:.4f}",)
    return RegistrationAssessment(
        source_id=source_id,
        source_region=source_region,
        target_region=target_region,
        status=RegistrationStatus.CANDIDATE,
        transform=transform,
        anatomical_match=anatomical_match,
        limitations=limitations,
    )


def promote_verified(assessment: RegistrationAssessment, *, evidence_ids: Iterable[str]) -> RegistrationAssessment:
    """Promote a candidate only with explicit anatomical and evidence gates."""
    if assessment.transform is None:
        raise ValueError("cannot verify registration without a candidate transform")
    ids = tuple(dict.fromkeys(x for x in evidence_ids if x))
    if not assessment.anatomical_match:
        raise ValueError("verified registration requires anatomical_match")
    if not ids:
        raise ValueError("verified registration requires evidence_ids")
    transform = SpatialTransform(
        transform_id=assessment.transform.transform_id,
        source_frame=assessment.transform.source_frame,
        target_frame=assessment.transform.target_frame,
        matrix=assessment.transform.matrix,
        method=assessment.transform.method,
        status=RegistrationStatus.VERIFIED,
        evidence_ids=ids,
        model_version=assessment.transform.model_version,
    )
    verified = RegistrationAssessment(
        source_id=assessment.source_id,
        source_region=assessment.source_region,
        target_region=assessment.target_region,
        status=RegistrationStatus.VERIFIED,
        transform=transform,
        anatomical_match=True,
        limitations=assessment.limitations,
    )
    verified.validate()
    return verified
