from pathlib import Path


PACKAGE_ROOT = Path(__file__).resolve().parents[1]


def test_initial_pose_is_published_before_waiting_for_nav2() -> None:
    """AMCL needs the initial pose before Nav2 global costmap can activate."""
    source = (PACKAGE_ROOT / "navbot_mission" / "multi_goal_nav.py").read_text(encoding="utf-8")
    run_body = source[source.index("    def run") : source.index("    def _publish_initial_pose")]

    publish_initial_pose = run_body.index("self._publish_initial_pose")

    assert publish_initial_pose < run_body.index("self.nav_client.wait_for_server")
    assert publish_initial_pose < run_body.index("self._wait_for_nav2_active")
