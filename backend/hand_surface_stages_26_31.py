"""Research-safe contracts for Hand Surface stages 26–31.

These stages close the gap between a validated projection handoff and an
explicit, auditable research run. They never reconstruct anatomy, infer
missing evidence, or turn biological observations into diagnostic claims.
"""
from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
from typing import Any, Mapping, Sequence

from .hand_surface_stages_21_25 import (
    ProjectionPlan,
    TwinPackage,
    build_reproducibility_record,
    validate_twin_package,
    validate_projection_plan,
)


@dataclass(frozen=True)
class EvidenceReference:
    evidence_id: str
    subject_id: str
    timepoint: str
    spatial_id: str
    biological_level: str | None = None


def _canonical(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def _fingerprint(value: Any) -> str:
    return sha256(_canonical(value).encode("utf-8")).hexdigest()


def validate_evidence_scope(
    references: Sequence[EvidenceReference],
    *,
    subject_id: str,
    timepoint: str,
    spatial_id: str,
    include_descendants: bool = True,
) -> dict[str, Any]:
    """Stage 26: validate evidence identity independently from biological level."""
    issues: list[str] = []
    seen: set[str] = set()
    direct = 0
    descendants = 0
    accepted: list[str] = []
    for ref in references:
        if not ref.evidence_id:
            issues.append("evidence reference is missing evidence_id")
            continue
        if ref.evidence_id in seen:
            issues.append(f"duplicate evidence_id: {ref.evidence_id}")
            continue
        seen.add(ref.evidence_id)
        if ref.subject_id != subject_id:
            issues.append(f"subject mismatch for {ref.evidence_id}")
            continue
        if ref.timepoint != timepoint:
            issues.append(f"timepoint mismatch for {ref.evidence_id}")
            continue
        if ref.spatial_id == spatial_id:
            direct += 1
            accepted.append(ref.evidence_id)
        elif include_descendants and ref.spatial_id.startswith(spatial_id.rstrip("/") + "/"):
            descendants += 1
            accepted.append(ref.evidence_id)
        else:
            issues.append(f"spatial scope mismatch for {ref.evidence_id}: {ref.spatial_id}")
    return {
        "schema": "hand-surface-evidence-scope-v1",
        "valid": not issues,
        "issues": issues,
        "scope": spatial_id,
        "include_descendants": include_descendants,
        "direct": direct,
        "descendants": descendants,
        "accepted_evidence_ids": accepted,
    }


def build_twin_manifest(package: TwinPackage, *, evidence_scope: Mapping[str, Any], software_version: str) -> dict[str, Any]:
    """Stage 27: create one explicit manifest joining package and evidence scope."""
    package_qa = validate_twin_package(package)
    payload = {
        "package": package.canonical_dict(),
        "evidence_scope": dict(evidence_scope),
        "software_version": software_version,
    }
    return {
        "schema": "digital-twin-research-manifest-v1",
        "identity": {
            "subject_id": package.subject_id,
            "timepoint": package.timepoint,
            "spatial_id": package.spatial_id,
            "coordinate_system": package.coordinate_system,
        },
        **payload,
        "package_valid": package_qa["valid"],
        "manifest_fingerprint": _fingerprint(payload),
        "accuracy_claim": False,
    }


def build_run_ledger_entry(*, run_id: str, manifest: Mapping[str, Any], worker_request: Mapping[str, Any], generated_at: str) -> dict[str, Any]:
    """Stage 28: record an auditable run without claiming execution."""
    status = "ready-for-execution" if worker_request.get("status") == "ready-for-worker" else "blocked"
    return {
        "schema": "hand-surface-run-ledger-v1",
        "run_id": run_id,
        "status": status,
        "generated_at": generated_at,
        "subject_id": manifest["identity"]["subject_id"],
        "timepoint": manifest["identity"]["timepoint"],
        "spatial_id": manifest["identity"]["spatial_id"],
        "manifest_fingerprint": manifest["manifest_fingerprint"],
        "worker_request_status": worker_request.get("status"),
        "execution_performed": False,
        "accuracy_claim": False,
    }


def build_research_bundle(*, manifest: Mapping[str, Any], worker_request: Mapping[str, Any], run_ledger: Mapping[str, Any], software_version: str, generated_at: str) -> dict[str, Any]:
    """Stage 29: assemble a portable metadata-only research bundle."""
    reproducibility = build_reproducibility_record(
        request={"manifest": dict(manifest), "worker_request": dict(worker_request), "run_id": run_ledger.get("run_id")},
        software_version=software_version,
        generated_at=generated_at,
    )
    bundle = {
        "schema": "hand-surface-research-bundle-v1",
        "manifest": dict(manifest),
        "worker_request": dict(worker_request),
        "run_ledger": dict(run_ledger),
        "reproducibility": reproducibility,
        "execution": {"performed": False, "accuracy_claim": False},
    }
    bundle["bundle_fingerprint"] = _fingerprint(bundle)
    return bundle


def validate_stage_acceptance(*, package: TwinPackage, plan: ProjectionPlan, manifest: Mapping[str, Any], worker_request: Mapping[str, Any], run_ledger: Mapping[str, Any]) -> dict[str, Any]:
    """Stage 30: final cross-contract acceptance gate."""
    issues: list[str] = []
    package_qa = validate_twin_package(package)
    plan_qa = validate_projection_plan(plan)
    issues.extend(f"package: {x}" for x in package_qa["issues"])
    issues.extend(f"projection: {x}" for x in plan_qa["issues"])
    if manifest.get("identity", {}).get("spatial_id") != package.spatial_id:
        issues.append("manifest spatial_id mismatch")
    if worker_request.get("spatial_id") != package.spatial_id:
        issues.append("worker request spatial_id mismatch")
    if run_ledger.get("spatial_id") != package.spatial_id:
        issues.append("run ledger spatial_id mismatch")
    if worker_request.get("execution", {}).get("performed") is not False:
        issues.append("worker execution flag must remain false")
    return {
        "schema": "hand-surface-acceptance-v1",
        "accepted": not issues,
        "issues": issues,
        "spatial_id": package.spatial_id,
        "subject_id": package.subject_id,
        "timepoint": package.timepoint,
    }


def build_research_trace(*, acceptance: Mapping[str, Any], bundle: Mapping[str, Any]) -> dict[str, Any]:
    """Stage 31: expose the complete research-safe trace in one object."""
    return {
        "schema": "hand-surface-research-trace-v1",
        "status": "accepted" if acceptance.get("accepted") else "blocked",
        "spatial_id": acceptance.get("spatial_id"),
        "subject_id": acceptance.get("subject_id"),
        "timepoint": acceptance.get("timepoint"),
        "acceptance": dict(acceptance),
        "bundle_fingerprint": bundle.get("bundle_fingerprint"),
        "execution_performed": False,
        "accuracy_claim": False,
        "scientific_boundary": "metadata and provenance only; no anatomy reconstruction or diagnosis",
    }
