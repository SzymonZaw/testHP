from backend.spatial_canonicalizer import canonical_spatial_id, spatial_ids_equal


def test_hypothenar_eminence_alias_resolves_to_contract_id():
    assert canonical_spatial_id("hand/palm/hypothenar-eminence") == "hand/palm/hypothenar"


def test_canonicalizer_does_not_invent_deeper_targets():
    assert canonical_spatial_id("hand/palm/hypothenar/hypothenar-field-a") == "hand/palm/hypothenar/hypothenar-field-a"


def test_alias_and_contract_id_compare_equal():
    assert spatial_ids_equal("/hand/palm/hypothenar-eminence/", "hand/palm/hypothenar")
