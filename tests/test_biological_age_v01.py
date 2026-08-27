from digital_twin.biological_age_v01 import AgeEvidence, estimate_biological_age


def test_multicomponent_age_uses_confidence_weighting_and_evidence():
    result = estimate_biological_age(
        morphology=AgeEvidence(42, .9, 2, "synthetic-morphology"),
        cellular=AgeEvidence(45, .7, 3, "synthetic-cellular"),
        functional=AgeEvidence(41, .4, 1, "synthetic-functional"),
    )

    expected = (42 * .9 + 45 * .7 + 41 * .4) / (.9 + .7 + .4)
    assert result.status == "estimated"
    assert result.overall_age == expected
    assert result.confidence == (.9 + .7 + .4) / 3
    assert result.evidence_count == 6


def test_missing_molecular_evidence_is_not_fabricated():
    result = estimate_biological_age(
        morphology=AgeEvidence(42, .9),
        cellular=AgeEvidence(45, .7),
    )

    assert result.status == "estimated"
    assert result.molecular is None
    assert result.evidence_count == 2


def test_insufficient_evidence_returns_no_overall_age():
    result = estimate_biological_age(
        cellular=AgeEvidence(45, .7, 4),
        minimum_components=2,
    )

    assert result.status == "insufficient_evidence"
    assert result.overall_age is None
    assert result.confidence == .7
    assert result.evidence_count == 4


def test_zero_confidence_components_do_not_create_a_false_estimate():
    result = estimate_biological_age(
        morphology=AgeEvidence(90, 0.0),
        cellular=AgeEvidence(40, 0.0),
    )

    assert result.status == "insufficient_evidence"
    assert result.overall_age is None
    assert result.confidence == 0.0
