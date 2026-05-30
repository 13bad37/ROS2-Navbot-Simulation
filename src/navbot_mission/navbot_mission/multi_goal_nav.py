from __future__ import annotations

import math
import sys
import time
import traceback
from pathlib import Path

import rclpy
from action_msgs.msg import GoalStatus
from ament_index_python.packages import get_package_share_directory
from geometry_msgs.msg import PoseStamped, PoseWithCovarianceStamped
from lifecycle_msgs.msg import State
from lifecycle_msgs.srv import GetState
from nav2_msgs.action import NavigateToPose
from nav_msgs.msg import Odometry
from rclpy.action import ActionClient
from rclpy.node import Node

from navbot_mission.goal_loader import NamedGoal, Pose2D, load_goal_file
from navbot_mission.metrics_logger import MissionMetricsLogger
from navbot_mission.odom_distance_tracker import (
    OdomDistanceTracker,
    PathMetrics,
    calculate_path_efficiency_pct,
)


class MultiGoalNavigator(Node):
    """
    ROS 2 Node that sequences a list of predefined navigation goals.

    This node reads a YAML file containing target poses, seeds AMCL with an
    initial pose, waits for Nav2 to become active, and then sequentially sends
    `NavigateToPose` action goals to the Nav2 stack. It also logs mission
    metrics via the `MissionMetricsLogger`.
    """

    def __init__(self) -> None:
        """
        Initialize the MultiGoalNavigator node.

        Sets up ROS parameters, publishers, action clients, and service clients
        required for interacting with the Nav2 stack.
        """
        super().__init__("multi_goal_nav")

        default_goals = str(Path(get_package_share_directory("navbot_mission")) / "config" / "goals.yaml")
        if not self.has_parameter("use_sim_time"):
            self.declare_parameter("use_sim_time", True)
        self.declare_parameter("goals_file", default_goals)
        self.declare_parameter("log_dir", "logs")
        self.declare_parameter("nav2_wait_timeout_sec", 90.0)
        self.declare_parameter("goal_timeout_sec", 180.0)
        self.declare_parameter("feedback_period_sec", 5.0)

        self.goals_file = Path(self.get_parameter("goals_file").value)
        self.log_dir = _resolve_log_dir(str(self.get_parameter("log_dir").value))
        self.nav2_wait_timeout_sec = float(self.get_parameter("nav2_wait_timeout_sec").value)
        self.goal_timeout_sec = float(self.get_parameter("goal_timeout_sec").value)
        self.feedback_period_sec = float(self.get_parameter("feedback_period_sec").value)

        self.initial_pose_pub = self.create_publisher(PoseWithCovarianceStamped, "/initialpose", 10)
        self.nav_client = ActionClient(self, NavigateToPose, "/navigate_to_pose")
        self.bt_state_client = self.create_client(GetState, "/bt_navigator/get_state")
        self.distance_tracker = OdomDistanceTracker()
        self.odom_sub = self.create_subscription(Odometry, "/odom", self._odom_callback, 20)
        self.latest_feedback = None

    def run(self) -> bool:
        """
        Execute the primary mission loop.

        Loads goals, waits for Nav2, iterates through each goal by sending it
        to the action server, logs the result, and writes a final mission summary.

        Returns:
            bool: True if all goals in the mission were successfully reached, False otherwise.
        """
        mission = load_goal_file(self.goals_file)
        metrics = MissionMetricsLogger(self.log_dir)
        metrics.start_mission()

        self.get_logger().info(f"Loaded {len(mission.goals)} goals from {self.goals_file}")

        if not self._wait_for_initial_pose_subscriber():
            metrics.record_goal("nav2_startup", 0.0, False, "/initialpose subscriber unavailable")
            log_path = metrics.finish_mission()
            self.get_logger().error(f"Wrote mission log: {log_path}")
            return False

        self._publish_initial_pose(mission.initial_pose)

        self.get_logger().info("Waiting for Nav2 NavigateToPose action server...")
        if not self.nav_client.wait_for_server(timeout_sec=self.nav2_wait_timeout_sec):
            self.get_logger().error(
                f"Nav2 action server was not ready after {self.nav2_wait_timeout_sec:.1f}s"
            )
            metrics.record_goal("nav2_startup", 0.0, False, "NavigateToPose action server unavailable")
            log_path = metrics.finish_mission()
            self.get_logger().error(f"Wrote mission log: {log_path}")
            return False

        if not self._wait_for_nav2_active():
            metrics.record_goal("nav2_startup", 0.0, False, "bt_navigator did not become active")
            log_path = metrics.finish_mission()
            self.get_logger().error(f"Wrote mission log: {log_path}")
            return False

        mission_started = time.monotonic()
        completed = 0
        total_traveled_distance_m = 0.0
        total_straight_line_distance_m = 0.0

        for index, goal in enumerate(mission.goals, start=1):
            self.get_logger().info(
                f"Goal {index}/{len(mission.goals)} {goal.name}: "
                f"x={goal.x:.2f} y={goal.y:.2f} yaw={goal.yaw:.2f}"
            )
            path_start = self.distance_tracker.snapshot()
            success, elapsed, message = self._navigate_to_goal(goal)
            path_metrics = self.distance_tracker.measure_since(path_start)
            total_traveled_distance_m += path_metrics.traveled_distance_m
            total_straight_line_distance_m += path_metrics.straight_line_distance_m
            metrics.record_goal(
                goal.name,
                elapsed,
                success,
                message,
                traveled_distance_m=path_metrics.traveled_distance_m,
                straight_line_distance_m=path_metrics.straight_line_distance_m,
                path_efficiency_pct=path_metrics.path_efficiency_pct,
            )
            if success:
                completed += 1
                self.get_logger().info(
                    f"Goal {goal.name} succeeded in {elapsed:.1f}s; {_path_metrics_text(path_metrics)}"
                )
            else:
                self.get_logger().error(
                    f"Goal {goal.name} failed in {elapsed:.1f}s: {message}; "
                    f"{_path_metrics_text(path_metrics)}"
                )

        log_path = metrics.finish_mission()
        total = time.monotonic() - mission_started
        mission_efficiency_pct = calculate_path_efficiency_pct(
            total_straight_line_distance_m,
            total_traveled_distance_m,
        )
        self.get_logger().info(
            f"Mission complete: {completed}/{len(mission.goals)} goals reached in {total:.1f}s; "
            f"traveled={total_traveled_distance_m:.2f}m "
            f"efficiency={_format_efficiency(mission_efficiency_pct)}"
        )
        self.get_logger().info(f"Wrote mission log: {log_path}")
        return completed == len(mission.goals)

    def _publish_initial_pose(self, pose: Pose2D) -> None:
        """
        Publish the initial pose of the robot for localization systems (e.g., AMCL).

        Args:
            pose (Pose2D): The initial 2D pose (x, y, yaw) to publish.
        """
        msg = PoseWithCovarianceStamped()
        msg.header.frame_id = "map"
        msg.pose.pose = _pose_from_2d(pose).pose
        msg.pose.covariance[0] = 0.02
        msg.pose.covariance[7] = 0.02
        msg.pose.covariance[35] = 0.02

        self.get_logger().info(
            f"Publishing initial pose: x={pose.x:.2f} y={pose.y:.2f} yaw={pose.yaw:.2f}"
        )
        for _ in range(8):
            msg.header.stamp = self.get_clock().now().to_msg()
            self.initial_pose_pub.publish(msg)
            rclpy.spin_once(self, timeout_sec=0.1)

    def _wait_for_initial_pose_subscriber(self) -> bool:
        """
        Wait for AMCL to subscribe to /initialpose before seeding localization.

        Nav2's global costmap cannot activate until AMCL publishes map->odom.
        Publishing the seed pose before waiting on bt_navigator avoids a startup
        deadlock after removing the old static map->odom transform.
        """
        self.get_logger().info("Waiting for AMCL /initialpose subscription...")
        deadline = time.monotonic() + self.nav2_wait_timeout_sec
        last_status_log = 0.0

        while rclpy.ok() and time.monotonic() < deadline:
            if self.initial_pose_pub.get_subscription_count() > 0:
                self.get_logger().info("AMCL is ready for the initial pose")
                return True

            now = time.monotonic()
            if now - last_status_log >= 5.0:
                last_status_log = now
                self.get_logger().info("Still waiting for AMCL to subscribe to /initialpose...")
            rclpy.spin_once(self, timeout_sec=0.2)

        self.get_logger().error(
            f"No /initialpose subscriber appeared after {self.nav2_wait_timeout_sec:.1f}s"
        )
        return False

    def _navigate_to_goal(self, goal: NamedGoal) -> tuple[bool, float, str]:
        """
        Send a single goal to the Nav2 action server and wait for the result.

        Args:
            goal (NamedGoal): The target goal containing x, y, yaw, and a name.

        Returns:
            tuple[bool, float, str]: A tuple containing:
                - success (bool): True if the goal was reached.
                - elapsed (float): The time taken in seconds.
                - status_name (str): The final status string (e.g., 'SUCCEEDED', 'ABORTED').
        """
        self.latest_feedback = None
        goal_msg = NavigateToPose.Goal()
        goal_msg.pose = _pose_from_2d(goal)
        goal_msg.pose.header.stamp = self.get_clock().now().to_msg()
        goal_msg.behavior_tree = ""

        start_time = time.monotonic()
        last_feedback_print = 0.0

        send_future = self.nav_client.send_goal_async(
            goal_msg,
            feedback_callback=self._feedback_callback,
        )
        rclpy.spin_until_future_complete(self, send_future)
        goal_handle = send_future.result()

        if goal_handle is None:
            return False, time.monotonic() - start_time, "No goal handle returned"
        if not goal_handle.accepted:
            return False, time.monotonic() - start_time, "Goal rejected by Nav2"

        self.get_logger().info(f"Goal {goal.name} accepted")
        result_future = goal_handle.get_result_async()

        while rclpy.ok() and not result_future.done():
            rclpy.spin_once(self, timeout_sec=0.2)
            elapsed = time.monotonic() - start_time
            if elapsed > self.goal_timeout_sec:
                self.get_logger().error(
                    f"Goal {goal.name} exceeded timeout of {self.goal_timeout_sec:.1f}s; canceling"
                )
                cancel_future = goal_handle.cancel_goal_async()
                rclpy.spin_until_future_complete(self, cancel_future)
                return False, elapsed, "Goal timed out"

            if elapsed - last_feedback_print >= self.feedback_period_sec and self.latest_feedback:
                last_feedback_print = elapsed
                feedback = self.latest_feedback.feedback
                self.get_logger().info(
                    f"Goal {goal.name} status: "
                    f"distance_remaining={feedback.distance_remaining:.2f}m "
                    f"navigation_time={_duration_sec(feedback.navigation_time):.1f}s "
                    f"recoveries={feedback.number_of_recoveries}"
                )

        elapsed = time.monotonic() - start_time
        result = result_future.result()
        status = result.status
        status_name = _goal_status_name(status)
        return status == GoalStatus.STATUS_SUCCEEDED, elapsed, status_name

    def _feedback_callback(self, feedback_msg) -> None:
        self.latest_feedback = feedback_msg

    def _odom_callback(self, msg: Odometry) -> None:
        position = msg.pose.pose.position
        self.distance_tracker.update(position.x, position.y)

    def _wait_for_nav2_active(self) -> bool:
        """
        Block until the bt_navigator node transitions to the ACTIVE lifecycle state.

        Returns:
            bool: True if bt_navigator became active within the timeout, False otherwise.
        """
        self.get_logger().info("Waiting for bt_navigator lifecycle state ACTIVE...")
        deadline = time.monotonic() + self.nav2_wait_timeout_sec
        last_status_log = 0.0

        while rclpy.ok() and time.monotonic() < deadline:
            if not self.bt_state_client.wait_for_service(timeout_sec=1.0):
                continue

            future = self.bt_state_client.call_async(GetState.Request())
            rclpy.spin_until_future_complete(self, future, timeout_sec=2.0)
            if not future.done() or future.result() is None:
                continue

            state = future.result().current_state
            if state.id == State.PRIMARY_STATE_ACTIVE:
                self.get_logger().info("bt_navigator is active")
                return True

            now = time.monotonic()
            if now - last_status_log >= 5.0:
                last_status_log = now
                self.get_logger().info(f"bt_navigator state: {state.label or state.id}")

        self.get_logger().error(
            f"bt_navigator was not active after {self.nav2_wait_timeout_sec:.1f}s"
        )
        return False


def _resolve_log_dir(value: str) -> Path:
    """
    Resolve the log directory string to an absolute Path object.

    Args:
        value (str): The directory path string (relative or absolute).

    Returns:
        Path: The absolute path to the directory.
    """
    path = Path(value).expanduser()
    if path.is_absolute():
        return path
    return Path.cwd() / path


def _pose_from_2d(pose: Pose2D) -> PoseStamped:
    """
    Convert a 2D pose (x, y, yaw) into a ROS geometry_msgs PoseStamped.

    Args:
        pose (Pose2D): The input 2D pose.

    Returns:
        PoseStamped: The corresponding PoseStamped message in the 'map' frame.
    """
    msg = PoseStamped()
    msg.header.frame_id = "map"
    msg.pose.position.x = pose.x
    msg.pose.position.y = pose.y
    msg.pose.position.z = 0.0
    msg.pose.orientation.z = math.sin(pose.yaw / 2.0)
    msg.pose.orientation.w = math.cos(pose.yaw / 2.0)
    return msg


def _duration_sec(duration_msg) -> float:
    return float(duration_msg.sec) + float(duration_msg.nanosec) / 1_000_000_000.0


def _path_metrics_text(metrics: PathMetrics) -> str:
    return (
        f"traveled={metrics.traveled_distance_m:.2f}m "
        f"straight_line={metrics.straight_line_distance_m:.2f}m "
        f"efficiency={_format_efficiency(metrics.path_efficiency_pct)}"
    )


def _format_efficiency(efficiency_pct: float | None) -> str:
    return f"{efficiency_pct:.1f}%" if efficiency_pct is not None else "n/a"


def _goal_status_name(status: int) -> str:
    names = {
        GoalStatus.STATUS_UNKNOWN: "UNKNOWN",
        GoalStatus.STATUS_ACCEPTED: "ACCEPTED",
        GoalStatus.STATUS_EXECUTING: "EXECUTING",
        GoalStatus.STATUS_CANCELING: "CANCELING",
        GoalStatus.STATUS_SUCCEEDED: "SUCCEEDED",
        GoalStatus.STATUS_CANCELED: "CANCELED",
        GoalStatus.STATUS_ABORTED: "ABORTED",
    }
    return names.get(status, f"STATUS_{status}")


def main() -> None:
    rclpy.init()
    node = MultiGoalNavigator()
    try:
        success = node.run()
    except KeyboardInterrupt:
        success = False
    except Exception as exc:
        node.get_logger().error(f"Mission failed with an unhandled error: {exc}")
        node.get_logger().error(traceback.format_exc())
        success = False
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()

    if not success:
        sys.exit(1)


if __name__ == "__main__":
    main()
