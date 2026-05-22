from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


@dataclass(frozen=True)
class Pose2D:
    """
    A 2D pose representation.

    Attributes:
        x (float): The X coordinate in meters.
        y (float): The Y coordinate in meters.
        yaw (float): The rotation around the Z axis in radians.
    """
    x: float
    y: float
    yaw: float


@dataclass(frozen=True)
class NamedGoal(Pose2D):
    """
    A 2D goal pose that includes a descriptive name.

    Attributes:
        name (str): The logical name of the goal (e.g., 'loading_dock').
    """
    name: str


@dataclass(frozen=True)
class MissionGoals:
    """
    Container for the complete mission definition.

    Attributes:
        initial_pose (Pose2D): The starting pose of the robot.
        goals (list[NamedGoal]): A sequential list of goals to navigate to.
    """
    initial_pose: Pose2D
    goals: list[NamedGoal]


def load_goal_file(path: str | Path) -> MissionGoals:
    """
    Load and parse mission poses from a YAML file.

    Args:
        path (str | Path): The path to the YAML configuration file.

    Returns:
        MissionGoals: The parsed initial pose and sequential goal list.

    Raises:
        FileNotFoundError: If the YAML file does not exist.
        ValueError: If the YAML structure is malformed or missing required fields.
    """
    goal_path = Path(path)
    if not goal_path.exists():
        raise FileNotFoundError(f"Goal file not found: {goal_path}")

    payload = yaml.safe_load(goal_path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"Goal file must contain a YAML mapping: {goal_path}")

    initial_pose = _load_pose(payload.get("initial_pose"), "initial_pose")
    raw_goals = payload.get("goals")
    if not isinstance(raw_goals, list) or not raw_goals:
        raise ValueError("Goal file must contain a non-empty 'goals' list")

    goals = []
    for index, raw_goal in enumerate(raw_goals, start=1):
        pose = _load_pose(raw_goal, f"goals[{index}]")
        name = str(raw_goal.get("name") or f"goal_{index}")
        goals.append(NamedGoal(name=name, x=pose.x, y=pose.y, yaw=pose.yaw))

    return MissionGoals(initial_pose=initial_pose, goals=goals)


def _load_pose(raw_pose: Any, label: str) -> Pose2D:
    if not isinstance(raw_pose, dict):
        raise ValueError(f"{label} must be a mapping with x, y, and yaw")

    return Pose2D(
        x=_required_float(raw_pose, "x", label),
        y=_required_float(raw_pose, "y", label),
        yaw=_required_float(raw_pose, "yaw", label),
    )


def _required_float(payload: dict[str, Any], key: str, label: str) -> float:
    if key not in payload:
        raise ValueError(f"{label} is missing required field '{key}'")
    try:
        return float(payload[key])
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{label}.{key} must be numeric") from exc

