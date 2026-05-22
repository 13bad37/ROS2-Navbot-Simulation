from __future__ import annotations

from copy import deepcopy

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import LaserScan


def rewrite_scan_frame(scan: LaserScan, frame_id: str) -> LaserScan:
    rewritten = deepcopy(scan)
    rewritten.header.frame_id = frame_id
    return rewritten


class ScanFrameRepublisher(Node):
    """Republish Gazebo lidar scans with the frame Nav2 expects."""

    def __init__(self) -> None:
        super().__init__("scan_frame_republisher")
        if not self.has_parameter("use_sim_time"):
            self.declare_parameter("use_sim_time", True)
        self.declare_parameter("input_topic", "/gz_scan_raw")
        self.declare_parameter("output_topic", "/scan")
        self.declare_parameter("frame_id", "lidar_link")

        self.frame_id = str(self.get_parameter("frame_id").value)
        input_topic = str(self.get_parameter("input_topic").value)
        output_topic = str(self.get_parameter("output_topic").value)

        self.publisher = self.create_publisher(LaserScan, output_topic, 10)
        self.subscription = self.create_subscription(LaserScan, input_topic, self._on_scan, 10)
        self.get_logger().info(
            f"Republishing {input_topic} to {output_topic} with frame_id={self.frame_id}"
        )

    def _on_scan(self, scan: LaserScan) -> None:
        self.publisher.publish(rewrite_scan_frame(scan, self.frame_id))


def main() -> None:
    rclpy.init()
    node = ScanFrameRepublisher()
    try:
        rclpy.spin(node)
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
