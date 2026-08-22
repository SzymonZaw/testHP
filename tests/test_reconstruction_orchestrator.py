from backend.reconstruction_orchestrator import run


def test_orchestrator_blocks_without_two_registered_views(monkeypatch):
    monkeypatch.setattr('backend.reconstruction_orchestrator._load_manifest', lambda: [
        {'subject_id': 's', 'timepoint': 't', 'registration': {'status': 'registered'}},
    ])
    result = run('s', 't')
    assert result['status'] == 'blocked'
    assert result['registered_count'] == 1
