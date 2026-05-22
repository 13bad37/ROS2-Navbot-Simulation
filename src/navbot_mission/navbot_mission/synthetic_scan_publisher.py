from __future__ import annotations

import math

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import LaserScan


class SyntheticScanPublisher(Node):
    """
    Publishes a simple planar scan for the stable portfolio demo path.

    This acts as a synthetic LiDAR, ensuring that Nav2 always receives a clear
    obstacle-free ring when there are no Gazebo obstacles, avoiding GPU ray
    sensor issues common in containerized environments.
    """

    def __init__(self) -> None:
        """Initialize the SyntheticScanPublisher and start the publishing timer."""
        super().__init__("synthetic_scan_publisher")
        if not self.has_parameter("use_sim_time"):
            self.declare_parameter("use_sim_time", True)
        self.declare_parameter("frame_id", "lidar_link")
        self.declare_parameter("range_m", 6.0)
        self.declare_parameter("samples", 720)
        self.declare_parameter("publish_rate_hz", 10.0)

        self.frame_id = str(self.get_parameter("frame_id").value)
        self.range_m = float(self.get_parameter("range_m").value)
        self.samples = int(self.get_parameter("samples").value)
        publish_rate_hz = float(self.get_parameter("publish_rate_hz").value)

        self.publisher = self.create_publisher(LaserScan, "/scan", 10)
        self.timer = self.create_timer(1.0 / publish_rate_hz, self._publish_scan)
        self.get_logger().info(
            f"Publishing synthetic /scan from {self.frame_id} at {publish_rate_hz:.1f} Hz"
        )

    def _publish_scan(self) -> None:
        """
        Construct and publish a 360-degree LaserScan message.
        """
        angle_min = -math.pi
        angle_max = math.pi
        scan = LaserScan()
        scan.header.stamp = self.get_clock().now().to_msg()
        scan.header.frame_id = self.frame_id
        scan.angle_min = angle_min
        scan.angle_max = angle_max
        scan.angle_increment = (angle_max - angle_min) / max(self.samples - 1, 1)
        scan.time_increment = 0.0
        scan.scan_time = 0.1
        scan.range_min = 0.12
        scan.range_max = 8.0
        scan.ranges = [self.range_m] * self.samples
        self.publisher.publish(scan)


def main() -> None:
    rclpy.init()
    node = SyntheticScanPublisher()
    try:
        rclpy.spin(node)
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
