from pathlib import Path

import pytest

from navbot_mission.goal_loader import load_goal_file


def test_load_goal_file_reads_initial_pose_and_goals(tmp_path: Path) -> None:
    goals_file = tmp_path / "goals.yaml"
    goals_file.write_text(
        """
initial_pose:
  x: -4.0
  y: -3.0
  yaw: 0.0
goals:
  - name: dock
    x: 3.0
    y: -2.5
    yaw: 1.57
""".strip(),
        encoding="utf-8",
    )

    mission = load_goal_file(goals_file)

    assert mission.initial_pose.x == -4.0
    assert mission.initial_pose.y == -3.0
    assert mission.goals[0].name == "dock"
    assert mission.goals[0].yaw == 1.57


def test_load_goal_file_rejects_missing_goals(tmp_path: Path) -> None:
    goals_file = tmp_path / "goals.yaml"
    goals_file.write_text("initial_pose: {x: 0.0, y: 0.0, yaw: 0.0}\n", encoding="utf-8")

    with pytest.raises(ValueError, match="goals"):
        load_goal_file(goals_file)

