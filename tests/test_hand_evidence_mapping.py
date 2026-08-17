from backend.hand_evidence_mapping import map_view_to_regions, region_links_dict


def test_front_view_maps_to_multiple_candidate_regions():
    links = map_view_to_regions("front")
    region_ids = {link.region_id for link in links}
    assert "palm" in region_ids
    assert "index" in region_ids
    assert len(region_ids) > 1
    assert all(link.method == "view_prior" for link in links)
    assert sum(link.confidence for link in links) == 1.0


def test_thumb_view_is_more_specific_but_still_explicitly_heuristic():
    links = map_view_to_regions("thumb")
    assert len(links) == 1
    assert links[0].region_id == "thumb"
    assert links[0].confidence == 1.0
    assert links[0].method == "view_prior"


def test_unknown_view_has_no_invented_region():
    assert map_view_to_regions("unknown") == []
    assert region_links_dict(None) == []
