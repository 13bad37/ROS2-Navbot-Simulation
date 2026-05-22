import json
from pathlib import Path

from navbot_mission.metrics_logger import MissionMetricsLogger


def test_metrics_logger_writes_summary_json(tmp_path: Path) -> None:
    logger = MissionMetricsLogger(tmp_path)
    logger.start_mission()
    logger.record_goal("dock", 12.5, True)
    logger.record_goal("inspection", 8.0, False)

    log_path = logger.finish_mission()

    payload = json.loads(log_path.read_text(encoding="utf-8"))
    assert payload["summary"]["total_goals"] == 2
    assert payload["summary"]["completed_goals"] == 1
    assert payload["summary"]["failed_goals"] == ["inspection"]
    assert payload["summary"]["average_time_per_goal_sec"] == 10.25

