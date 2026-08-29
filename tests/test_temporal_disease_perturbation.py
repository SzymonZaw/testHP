from integrations.temporal_disease_perturbation import (
    ALL,
    get_integration,
    list_integrations,
)


def test_new_research_integrations_are_registered():
    assert {x.name for x in ALL} == {
        "MaxToki", "TEDDY", "KRONOS", "TxPert", "ChrisCell", "scLong"
    }


def test_lookup_is_case_insensitive():
    assert get_integration("maxtoki").name == "MaxToki"
    assert get_integration("KRONOS").name == "KRONOS"


def test_all_items_have_metadata():
    for item in list_integrations():
        assert item.capability
        assert item.source.startswith("https://")
        assert item.license_note
