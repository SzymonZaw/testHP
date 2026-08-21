"""Research-safe contracts for Hand Surface stages 21–25.

Stages 21–25 turn the existing registration/projection metadata into an
explicit, auditable hand-surface handoff. They validate plans and packages,
create a deterministic worker request, and record reproducibility metadata.
No function in this module reconstructs anatomy or invents missing evidence.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from hashlib import sha256
import json
from typing import Any, Mapping

from .hand_surface_pipeline import COORDINATE_SYSTEM, SUPPORTED_VIEWS


@dataclass(frozen=True)
class ProjectionViewPlan:
    view: str
    quality: float = 0.0
    prepared: bool = False
    weight: float = 0.0

    @property
    def usable(self) -> bool:
        return self.view in SUPPORTED_VIEWS and self.prepared and self.quality > 0 and self.weight > 0


@dataclass(frozen=True)
class ProjectionPlan:
    target: str
    views: tuple[ProjectionViewPlan, ...] = ()
    confidence: float = 0.0
    mode: str = "weighted-multiview-plan"
    schema: str = "surface-projection-v2"

    def validate(self) -> list[str]:
        issues: list[str] = []
        if not self.target:
            issues.append("projection target is missing")
        if self.mode != "weighted-multiview-plan":
            issues.append("unsupported projection mode")
        if not 0 <= self.confidence <= 1:
            issues.append("projection confidence must be between 0 and 1")
        seen: set[str] = set()
        for view in self.views:
            if view.view in seen:
                issues.append(f"duplicate projection view: {view.view}")
            seen.add(view.view)
            if view.view not in SUPPORTED_VIEWS:
                issues.append(f"unsupported projection view: {view.view}")
            if not 0 <= view.quality <= 1:
                issues.append(f"invalid quality for {view.view}")
            if not 0 <= view.weight <= 1:
                issues.append(f"invalid weight for {view.view}")
        return issues

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema": self.schema,
            "mode": self.mode,
            "target": self.target,
            "confidence": self.confidence,
            "views": [asdict(view) for view in self.views],
        }


def validate_projection_plan(plan: ProjectionPlan, *, minimum_views: int = 2) -> dict[str, Any]:
    """Stage 21: validate a source-selection plan without performing projection."""
    issues = plan.validate()
    usable = [view for view in plan.views if view.usable]
    if len(usable) < minimum_views:
        issues.append(f"at least {minimum_views} usable prepared views are required for projection testing")
    if plan.confidence < 0.5:
        issues.append("projection confidence is below the review threshold")
    return {
        "schema": "surface-projection-plan-qa-v1",
        "valid": not issues,
        "issues": issues,
        "usable_views": [view.view for view in usable],
        "minimum_views": minimum_views,
        "confidence": plan.confidence,
        "accuracy_claim": False,
    }


@dataclass(frozen=True)
class TwinPackage:
    subject_id: str
    timepoint: str
    spatial_id: str
    coordinate_system: str = COORDINATE_SYSTEM
    geometry: Mapping[str, Any] = field(default_factory=dict)
    mappings: tuple[Mapping[str, Any], ...] = ()
    projection_plan: Mapping[str, Any] = field(default_factory=dict)
    evidence_ids: tuple[str, ...] = ()
    provenance: Mapping[str, Any] = field(default_factory=dict)
    schema: str = "digital-twin-hand-surface-package-v2"

    def canonical_dict(self) -> dict[str, Any]:
        return {
            "schema": self.schema,
            "subject_id": self.subject_id,
            "timepoint": self.timepoint,
            "spatial_id": self.spatial_id,
            "coordinate_system": self.coordinate_system,
            "geometry": dict(self.geometry),
            "mappings": [dict(x) for x in self.mappings],
            "projection_plan": dict(self.projection_plan),
            "evidence_ids": sorted(set(self.evidence_ids)),
            "provenance": dict(self.provenance),
        }


def validate_twin_package(package: TwinPackage) -> dict[str, Any]:
    """Stage 22/23: validate package identity, spatial target and evidence references."""
    issues: list[str] = []
    if not package.subject_id:
        issues.append("subject_id is missing")
    if not package.timepoint:
        issues.append("timepoint is missing")
    if not package.spatial_id:
        issues.append("spatial_id is missing")
    if package.coordinate_system != COORDINATE_SYSTEM:
        issues.append("coordinate system mismatch")
    if not package.evidence_ids:
        issues.append("package contains no evidence identifiers")
    if not package.projection_plan:
        issues.append("projection plan is missing")
    return {
        "schema": "digital-twin-package-qa-v1",
        "valid": not issues,
        "issues": issues,
        "evidence_count": len(set(package.evidence_ids)),
        "spatial_id": package.spatial_id,
    }


def build_projection_worker_request(package: TwinPackage, plan: ProjectionPlan) -> dict[str, Any]:
    """Stage 24: create an explicit worker handoff; this does not execute it."""
    package_qa = validate_twin_package(package)
    plan_qa = validate_projection_plan(plan)
    return {
        "schema": "hand-surface-projection-request-v1",
        "status": "ready-for-worker" if package_qa["valid"] and plan_qa["valid"] else "blocked",
        "subject_id": package.subject_id,
        "timepoint": package.timepoint,
        "spatial_id": package.spatial_id,
        "coordinate_system": package.coordinate_system,
        "projection_plan": plan.to_dict(),
        "evidence_ids": sorted(set(package.evidence_ids)),
        "qa": {"package": package_qa, "plan": plan_qa},
        "execution": {"performed": False, "accuracy_claim": False},
    }


def reproducibility_fingerprint(payload: Mapping[str, Any]) -> str:
    """Stage 25: deterministic fingerprint for an exported research run."""
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return sha256(canonical.encode("utf-8")).hexdigest()


def build_reproducibility_record(*, request: Mapping[str, Any], software_version: str, generated_at: str) -> dict[str, Any]:
    """Record inputs and software identity without pretending to reproduce pixels."""
    payload = {
        "schema": "hand-surface-reproducibility-v1",
        "software_version": software_version,
        "generated_at": generated_at,
        "request": dict(request),
    }
    payload["fingerprint"] = reproducibility_fingerprint(payload)
    payload["accuracy_claim"] = False
    return payload
