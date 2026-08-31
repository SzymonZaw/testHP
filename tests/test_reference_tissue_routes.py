from fastapi.testclient import TestClient

from backend.app import app

client = TestClient(app)


def test_reference_tissue_sources_manifest():
    response = client.get('/api/reference/tissue/sources')
    assert response.status_code == 200
    payload = response.json()
    assert payload['handReferenceId'] == 'nih-hand-template-3DPX-017237'
    assert any(source['id'] == 'human-skin-spatial-census' for source in payload['sources'])


def test_human_skin_spatial_census_is_manifest_only():
    response = client.get('/api/reference/tissue/human-skin-spatial-census')
    assert response.status_code == 200
    payload = response.json()
    source = payload['source']
    assert source['registrationStatus'] == 'unregistered_to_hand'
    assert source['registrationReadiness'] == 'anatomical_match_verified_transform_missing'
    assert source['coordinateScope'] == 'sample_local'
    assert payload['dataLoadStatus'] == 'manifest_only'
    assert payload['tissueIds'] == []
    assert payload['spatialCoordinates'] == []
    assert payload['transform'] is None


def test_unknown_reference_tissue_source_is_404():
    response = client.get('/api/reference/tissue/does-not-exist')
    assert response.status_code == 404
