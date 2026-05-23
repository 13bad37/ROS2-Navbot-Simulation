from pathlib import Path


PACKAGE_ROOT = Path(__file__).resolve().parents[1]


def read_package_file(relative_path: str) -> str:
    return (PACKAGE_ROOT / relative_path).read_text(encoding="utf-8")


def test_sim_launch_exposes_gui_and_scan_source_toggles() -> None:
    launch_text = read_package_file("launch/sim.launch.py")

    assert 'DeclareLaunchArgument("gui"' in launch_text
    assert 'DeclareLaunchArgument("use_synthetic_scan", default_value="false")' in launch_text
    assert "IfCondition(gui)" in launch_text
    assert "IfCondition(use_synthetic_scan)" in launch_text
    assert "UnlessCondition(use_synthetic_scan)" in launch_text


def test_demo_launch_defaults_to_gazebo_lidar() -> None:
    launch_text = read_package_file("launch/demo.launch.py")

    assert 'DeclareLaunchArgument("use_synthetic_scan", default_value="false")' in launch_text


def test_bridge_config_has_optional_gazebo_scan_mapping() -> None:
    bridge_text = read_package_file("config/ros_gz_scan_bridge.yaml")

    assert 'ros_topic_name: "/gz_scan_raw"' in bridge_text
    assert 'gz_topic_name: "/gz_scan"' in bridge_text
    assert 'ros_type_name: "sensor_msgs/msg/LaserScan"' in bridge_text
    assert 'gz_type_name: "gz.msgs.LaserScan"' in bridge_text
    assert "direction: GZ_TO_ROS" in bridge_text


def test_nav_launch_uses_amcl_instead_of_static_map_transform() -> None:
    launch_text = read_package_file("launch/nav.launch.py")

    assert 'package="nav2_amcl"' in launch_text
    assert '"node_names": ["map_server", "amcl"]' in launch_text
    assert "static_transform_publisher" not in launch_text
