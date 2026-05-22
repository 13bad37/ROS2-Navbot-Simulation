from sensor_msgs.msg import LaserScan

from navbot_mission.scan_frame_republisher import rewrite_scan_frame


def test_rewrite_scan_frame_sets_nav2_frame_without_mutating_input() -> None:
    scan = LaserScan()
    scan.header.frame_id = "navbot/raw_lidar_frame"
    scan.ranges = [1.0, 2.0, 3.0]

    rewritten = rewrite_scan_frame(scan, "lidar_link")

    assert rewritten.header.frame_id == "lidar_link"
    assert rewritten.ranges == scan.ranges
    assert scan.header.frame_id == "navbot/raw_lidar_frame"
