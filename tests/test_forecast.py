from geostream.forecast import Point, project, rolling_mean


def _series(values):
    return [Point(f"2026-01-{i + 1:02d}", v) for i, v in enumerate(values)]


def test_rolling_mean_smooths():
    series = _series([0.0, 2.0, 4.0])
    out = rolling_mean(series, window=2)
    assert out[0].value == 0.0
    assert out[1].value == 1.0
    assert out[2].value == 3.0


def test_project_needs_enough_history():
    assert project(_series([1.0, 2.0])) == ([], None)


def test_project_extrapolates_upward_trend():
    # Realistic anomaly magnitudes (within the +/-3 C clamp).
    series = _series([round(i * 0.1, 2) for i in range(14)])
    points, trend = project(series, horizon_days=14)
    assert points, "expected projection points"
    assert trend is not None and trend > 0
    assert points[-1].value > series[-1].value
    assert all(-3.0 <= p.value <= 3.0 for p in points)
