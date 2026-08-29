from integrations.ageing_and_multimodal import (
    ALL,
    SCAGECLOCK,
    SCICORE_OMICS,
    SPATIAL_AGING_CLOCK,
    SUBCELL,
    get_integration,
    list_integrations,
)


def test_all_four_integrations_are_registered():
    assert {item.name for item in ALL} == {
        "scAgeClock",
        "Spatial Aging Clocks",
        "SubCell",
        "SciCore-Omics",
    }


def test_lookup_is_case_insensitive():
    assert get_integration("scageclock") == SCAGECLOCK
    assert get_integration("SUBCELL") == SUBCELL


def test_catalog_contains_sources_and_capabilities():
    for item in list_integrations():
        assert item.source.startswith("https://")
        assert item.capability
        assert item.license_note


def test_expected_items_are_available():
    assert get_integration("Spatial Aging Clocks") == SPATIAL_AGING_CLOCK
    assert get_integration("SciCore-Omics") == SCICORE_OMICS
