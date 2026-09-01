from backend.merfish_region_mapping import (
    exact_source_sites,
    get_mapping,
    matches_anatomic_site,
    matches_sample_compartment,
)


def test_hand_digit_regions_have_no_false_exact_mapping():
    for region in ("wrist", "palm", "thumb", "index", "middle", "ring", "little"):
        assert exact_source_sites(region) == ()
        assert not matches_anatomic_site(region, "forearm")
        assert not matches_anatomic_site(region, "elbow")


def test_elbow_is_an_exact_h5ad_site_but_not_a_hand_ui_zone():
    assert get_mapping("elbow").anatomic_sites == ("elbow",)
    assert matches_anatomic_site("elbow", "elbow")
    assert not matches_anatomic_site("elbow", "forearm")


def test_skin_regions_uses_observed_h5ad_sites():
    assert matches_anatomic_site("skin_regions", "forearm")
    assert matches_anatomic_site("skin_regions", "elbow")
    assert matches_anatomic_site("skin_regions", "sole")
    assert not matches_anatomic_site("skin_regions", "middle")


def test_mapping_is_case_and_whitespace_insensitive():
    assert get_mapping("  PALM ").ui_region == "palm"
    assert matches_anatomic_site(" SKIN_REGIONS ", "Forearm")
    assert matches_anatomic_site("ELBOW", "Elbow")


def test_sample_compartment_filter_is_explicit_and_not_inferred_for_hand_zones():
    assert not matches_sample_compartment("palm", "dermis")
    assert not matches_sample_compartment("middle", "epidermis")
    assert not matches_sample_compartment("elbow", "dermis")
