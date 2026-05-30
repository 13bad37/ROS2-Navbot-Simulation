from __future__ import annotations

import math
from dataclasses import dataclass


@dataclass(frozen=True)
class OdomSnapshot:
    x: float | None
    y: float | None
    total_distance_m: float


@dataclass(frozen=True)
class PathMetrics:
    traveled_distance_m: float
    straight_line_distance_m: float
    path_efficiency_pct: float | None


class OdomDistanceTracker:
    """Accumulates robot travel distance from consecutive odometry samples."""

    def __init__(self) -> None:
        self._x: float | None = None
        self._y: float | None = None
        self._total_distance_m = 0.0

    def update(self, x: float, y: float) -> None:
        if self._x is not None and self._y is not None:
            self._total_distance_m += math.hypot(x - self._x, y - self._y)
        self._x = float(x)
        self._y = float(y)

    def snapshot(self) -> OdomSnapshot:
        return OdomSnapshot(x=self._x, y=self._y, total_distance_m=self._total_distance_m)

    def measure_since(self, start: OdomSnapshot) -> PathMetrics:
        traveled = max(0.0, self._total_distance_m - start.total_distance_m)
        if start.x is None or start.y is None or self._x is None or self._y is None:
            straight_line = 0.0
        else:
            straight_line = math.hypot(self._x - start.x, self._y - start.y)

        return PathMetrics(
            traveled_distance_m=round(traveled, 3),
            straight_line_distance_m=round(straight_line, 3),
            path_efficiency_pct=calculate_path_efficiency_pct(straight_line, traveled),
        )


def calculate_path_efficiency_pct(straight_line_distance_m: float, traveled_distance_m: float) -> float | None:
    if traveled_distance_m <= 0.0:
        return None
    return round(min(straight_line_distance_m / traveled_distance_m, 1.0) * 100.0, 3)
