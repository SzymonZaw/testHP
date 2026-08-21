from backend.hand_surface_stages_21_25 import (
    ProjectionPlan,
    ProjectionViewPlan,
    TwinPackage,
    build_projection_worker_request,
    build_reproducibility_record,
    reproducibility_fingerprint,
    validate_projection_plan,
    validate_twin_package,
)


def good_plan():
    return ProjectionPlan(
        target="hand/palm",
        confidence=0.8,
        views=(
            ProjectionViewPlan("front", 0.9, True, 0.8),
            ProjectionViewPlan("back", 0.8, True, 0.7),
        ),
    )


def good_package():
    return TwinPackage(
        subject_id="own_cohort",
        timepoint="T0",
        spatial_id="hand/palm",
        projection_plan=good_plan().to_dict(),
        evidence_ids=("evidence-a", "evidence-b"),
        provenance={"source": "test"},
    )


def test_stage_21_accepts_two_prepared_views():
    result = validate_projection_plan(good_plan())
    assert result["valid"] is True
    assert result["usable_views"] == ["front", "back"]
    assert result["accuracy_claim"] is False


def test_stage_21_blocks_insufficient_views():
    plan = ProjectionPlan(
        target="hand/palm",
        confidence=0.8,
        views=(ProjectionViewPlan("front", 0.9, True, 0.8),),
    )
    result = validate_projection_plan(plan)
    assert result["valid"] is False


def test_stage_22_23_requires_spatial_identity_and_evidence():
    result = validate_twin_package(good_package())
    assert result["valid"] is True
    assert result["spatial_id"] == "hand/palm"
    assert result["evidence_count"] == 2


def test_stage_24_blocks_bad_handoff():
    package = TwinPackage(subject_id="own_cohort", timepoint="T0", spatial_id="hand/palm")
    request = build_projection_worker_request(package, good_plan())
    assert request["status"] == "blocked"
    assert request["execution"]["performed"] is False


def test_stage_24_creates_research_safe_handoff():
    request = build_projection_worker_request(good_package(), good_plan())
    assert request["status"] == "ready-for-worker"
    assert request["spatial_id"] == "hand/palm"
    assert request["execution"]["accuracy_claim"] is False


def test_stage_25_fingerprint_is_deterministic():
    payload = {"spatial_id": "hand/palm", "views": ["front", "back"]}
    assert reproducibility_fingerprint(payload) == reproducibility_fingerprint(payload)
    record = build_reproducibility_record(
        request=payload,
        software_version="test",
        generated_at="2026-08-21T00:00:00Z",
    )
    assert len(record["fingerprint"]) == 64
    assert record["accuracy_claim"] is False
