from integrations.multiscale_virtual_cell import ALL, get_integration


def test_next_wave_integrations_are_registered():
    assert {x.name for x in ALL} == {
        "TERRA", "CAPTAIN", "Stack", "Perturb Sapiens", "VirTues",
        "DeepSpot2Cell", "CellViT++", "InstanSeg", "stAge", "VirtualCell",
    }


def test_lookup_is_case_insensitive():
    assert get_integration("terra").name == "TERRA"
    assert get_integration("captain").name == "CAPTAIN"
    assert get_integration("stack").name == "Stack"


def test_all_items_have_capability_and_source():
    for item in ALL:
        assert item.capability
        assert item.source.startswith("https://")
