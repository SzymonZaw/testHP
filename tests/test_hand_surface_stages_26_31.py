from backend.hand_surface_stages_21_25 import ProjectionPlan, ProjectionViewPlan, TwinPackage
from backend.hand_surface_stages_26_31 import (
    EvidenceReference,
    build_research_bundle,
    build_research_trace,
    build_run_ledger_entry,
    build_twin_manifest,
    validate_evidence_scope,
    validate_stage_acceptance,
)


def plan():
    return ProjectionPlan(
        target="hand/palm",
        confidence=0.8,
        views=(
            ProjectionViewPlan("front", 0.9, True, 0.8),
            ProjectionViewPlan("back", 0.8, True, 0.7),
        ),
    )


def package():
    return TwinPackage(
        subject_id="own_cohort",
        timepoint="T0",
        spatial_id="hand/palm",
        projection_plan=plan().to_dict(),
        evidence_ids=("evidence-a", "evidence-b"),
    )


def evidence():
    return [
        EvidenceReference("evidence-a", "own_cohort", "T0", "hand/palm", "cellular"),
        EvidenceReference("evidence-b", "own_cohort", "T0", "hand/palm/central-palm", "cellular"),
    ]


def test_stage_26_separates_direct_and_descendant_evidence():
    result = validate_evidence_scope(evidence(), subject_id="own_cohort", timepoint="T0", spatial_id="hand/palm")
    assert result["valid"] is True
    assert result["direct"] == 1
    assert result["descendants"] == 1


def test_stage_26_rejects_sibling_evidence():
    refs = evidence() + [EvidenceReference("evidence-x", "own_cohort", "T0", "hand/thumb", "cellular")]
    result = validate_evidence_scope(refs, subject_id="own_cohort", timepoint="T0", spatial_id="hand/palm")
    assert result["valid"] is False
    assert any("spatial scope mismatch" in issue for issue in result["issues"])


def test_stages_27_to_29_build_consistent_manifest_bundle():
    scope = validate_evidence_scope(evidence(), subject_id="own_cohort", timepoint="T0", spatial_id="hand/palm")
    manifest = build_twin_manifest(package(), evidence_scope=scope, software_version="test")
    worker = {
        "status": "ready-for-worker",
        "spatial_id": "hand/palm",
        "execution": {"performed": False},
    }
    ledger = build_run_ledger_entry(
        run_id="run-26-31",
        manifest=manifest,
        worker_request=worker,
        generated_at="2026-08-21T00:00:00Z",
    )
    bundle = build_research_bundle(
        manifest=manifest,
        worker_request=worker,
        run_ledger=ledger,
        software_version="test",
        generated_at="2026-08-21T00:00:00Z",
    )
    assert manifest["identity"]["spatial_id"] == "hand/palm"
    assert ledger["status"] == "ready-for-execution"
    assert len(bundle["bundle_fingerprint"]) == 64
    assert bundle["execution"]["performed"] is False


def test_stage_30_accepts_matching_contracts():
    scope = validate_evidence_scope(evidence(), subject_id="own_cohort", timepoint="T0", spatial_id="hand/palm")
    manifest = build_twin_manifest(package(), evidence_scope=scope, software_version="test")
    worker = {"status": "ready-for-worker", "spatial_id": "hand/palm", "execution": {"performed": False}}
    ledger = build_run_ledger_entry(run_id="run", manifest=manifest, worker_request=worker, generated_at="now")
    result = validate_stage_acceptance(package=package(), plan=plan(), manifest=manifest, worker_request=worker, run_ledger=ledger)
    assert result["accepted"] is True


def test_stage_31_blocks_inconsistent_trace():
    acceptance = {"accepted": False, "spatial_id": "hand/palm", "subject_id": "own_cohort", "timepoint": "T0", "issues": ["test"]}
    trace = build_research_trace(acceptance=acceptance, bundle={"bundle_fingerprint": "abc"})
    assert trace["status"] == "blocked"
    assert trace["execution_performed"] is False
