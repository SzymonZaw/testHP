from backend.visual_hull import build_visual_hull


def _record(view):
    return {
        'view': view,
        'status': 'registered',
        'registration': {
            'status': 'registered',
            'quality': 0.9,
            'landmarks': [
                {'x': 0.2, 'y': 0.2, 'z': 0},
                {'x': 0.8, 'y': 0.2, 'z': 0},
                {'x': 0.5, 'y': 0.8, 'z': 0},
                {'x': 0.5, 'y': 0.5, 'z': 0},
            ],
        },
    }


def test_visual_hull_requires_two_views():
    try:
        build_visual_hull([_record('front')])
    except ValueError as exc:
        assert 'two' in str(exc).lower()
    else:
        raise AssertionError('expected two-view validation')


def test_visual_hull_generates_mesh():
    mesh = build_visual_hull([_record('front'), _record('back')], resolution=12)
    assert mesh['method'] == 'silhouette-envelope-v1'
    assert len(mesh['vertices']) > 0
    assert len(mesh['faces']) > 0
