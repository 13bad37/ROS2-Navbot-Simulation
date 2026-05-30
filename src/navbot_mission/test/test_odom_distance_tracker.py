import pytest

from navbot_mission.odom_distance_tracker import OdomDistanceTracker


def test_tracker_measures_distance_and_path_efficiency() -> None:
    tracker = OdomDistanceTracker()
    tracker.update(0.0, 0.0)
    start = tracker.snapshot()

    tracker.update(3.0, 0.0)
    tracker.update(3.0, 4.0)

    metrics = tracker.measure_since(start)

    assert metrics.traveled_distance_m == 7.0
    assert metrics.straight_line_distance_m == 5.0
    assert metrics.path_efficiency_pct == pytest.approx(71.429, abs=0.001)


def test_tracker_reports_no_efficiency_without_motion() -> None:
    tracker = OdomDistanceTracker()
    tracker.update(1.0, 2.0)

    metrics = tracker.measure_since(tracker.snapshot())

    assert metrics.traveled_distance_m == 0.0
    assert metrics.straight_line_distance_m == 0.0
    assert metrics.path_efficiency_pct is None
