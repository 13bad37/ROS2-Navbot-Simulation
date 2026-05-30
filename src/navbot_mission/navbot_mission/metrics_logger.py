from __future__ import annotations

import json
import time
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path

from navbot_mission.odom_distance_tracker import calculate_path_efficiency_pct


@dataclass(frozen=True)
class GoalResult:
    """
    Records the outcome of a single navigation goal.

    Attributes:
        name (str): The name of the goal.
        elapsed_sec (float): Time taken to reach or fail the goal in seconds.
        success (bool): True if the goal was successfully reached.
        message (str): Additional status information or failure reason.
        traveled_distance_m (float): Distance measured from odometry during the goal.
        straight_line_distance_m (float): Direct displacement measured during the goal.
        path_efficiency_pct (float | None): Direct displacement as a percentage of travel distance.
    """
    name: str
    elapsed_sec: float
    success: bool
    message: str
    traveled_distance_m: float
    straight_line_distance_m: float
    path_efficiency_pct: float | None


class MissionMetricsLogger:
    """
    Logs navigation performance metrics to a JSON file.

    Tracks mission start/end times and the success/failure state of individual
    goals. Generates a comprehensive summary at the end of the mission.
    """

    def __init__(self, log_dir: str | Path) -> None:
        """
        Initialize the logger.

        Args:
            log_dir (str | Path): Directory where the JSON logs will be written.
        """
        self.log_dir = Path(log_dir)
        self._started_at_wall: datetime | None = None
        self._started_at_mono: float | None = None
        self._goal_results: list[GoalResult] = []

    def start_mission(self) -> None:
        """
        Start the mission timer and initialize the storage arrays.
        Creates the log directory if it does not exist.
        """
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self._started_at_wall = _utc_now()
        self._started_at_mono = time.monotonic()
        self._goal_results = []

    def record_goal(
        self,
        name: str,
        elapsed_sec: float,
        success: bool,
        message: str = "",
        *,
        traveled_distance_m: float = 0.0,
        straight_line_distance_m: float = 0.0,
        path_efficiency_pct: float | None = None,
    ) -> None:
        """
        Record the completion or failure of a navigation goal.

        Args:
            name (str): The name of the goal.
            elapsed_sec (float): Time taken to process the goal.
            success (bool): Whether the goal succeeded.
            message (str, optional): Additional status text. Defaults to "".
            traveled_distance_m (float, optional): Odom distance covered during the goal.
            straight_line_distance_m (float, optional): Direct displacement during the goal.
            path_efficiency_pct (float | None, optional): Direct displacement divided by travel distance.
        """
        self._goal_results.append(
            GoalResult(
                name=name,
                elapsed_sec=round(float(elapsed_sec), 3),
                success=bool(success),
                message=message,
                traveled_distance_m=round(float(traveled_distance_m), 3),
                straight_line_distance_m=round(float(straight_line_distance_m), 3),
                path_efficiency_pct=(
                    round(float(path_efficiency_pct), 3) if path_efficiency_pct is not None else None
                ),
            )
        )

    def finish_mission(self) -> Path:
        """
        Conclude the mission, calculate summary statistics, and write the JSON file.

        Returns:
            Path: The absolute path to the generated JSON log file.

        Raises:
            RuntimeError: If `finish_mission` is called before `start_mission`.
        """
        if self._started_at_wall is None or self._started_at_mono is None:
            raise RuntimeError("start_mission() must be called before finish_mission()")

        finished_at = _utc_now()
        total_time = round(time.monotonic() - self._started_at_mono, 3)
        completed = [goal for goal in self._goal_results if goal.success]
        failed = [goal.name for goal in self._goal_results if not goal.success]
        average = (
            round(sum(goal.elapsed_sec for goal in self._goal_results) / len(self._goal_results), 3)
            if self._goal_results
            else 0.0
        )
        total_traveled = round(sum(goal.traveled_distance_m for goal in self._goal_results), 3)
        total_straight_line = round(
            sum(goal.straight_line_distance_m for goal in self._goal_results),
            3,
        )

        payload = {
            "started_at": self._started_at_wall.isoformat(),
            "finished_at": finished_at.isoformat(),
            "goals": [asdict(goal) for goal in self._goal_results],
            "summary": {
                "total_goals": len(self._goal_results),
                "completed_goals": len(completed),
                "total_mission_time_sec": total_time,
                "average_time_per_goal_sec": average,
                "failed_goals": failed,
                "total_traveled_distance_m": total_traveled,
                "total_straight_line_distance_m": total_straight_line,
                "mission_path_efficiency_pct": calculate_path_efficiency_pct(
                    total_straight_line,
                    total_traveled,
                ),
            },
        }

        filename = f"mission_{finished_at.strftime('%Y-%m-%dT%H-%M-%S')}.json"
        log_path = self.log_dir / filename
        log_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
        return log_path


def _utc_now() -> datetime:
    return datetime.now(timezone.utc).replace(microsecond=0)
