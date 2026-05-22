import os
from pathlib import Path

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, ExecuteProcess, SetEnvironmentVariable, TimerAction
from launch.conditions import IfCondition, UnlessCondition
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    """
    Launch Gazebo Harmonic, spawn the NavBot, and configure ROS-Gazebo bridges.

    This launch file handles the low-level simulation components:
    1. Setting up Gazebo resource paths.
    2. Starting the Gazebo server and GUI.
    3. Spawning the robot model into the world.
    4. Publishing the robot state (URDF).
    5. Bridging topics (odometry, cmd_vel, tf) between ROS 2 and Gazebo.
    6. Starting either the synthetic scan publisher or the optional Gazebo scan bridge.
    """
    bringup_dir = Path(get_package_share_directory("navbot_bringup"))
    description_dir = Path(get_package_share_directory("navbot_description"))

    # Launch Arguments
    world = LaunchConfiguration("world")
    robot_name = LaunchConfiguration("robot_name")
    use_sim_time = LaunchConfiguration("use_sim_time")
    gui = LaunchConfiguration("gui")
    use_synthetic_scan = LaunchConfiguration("use_synthetic_scan")

    default_world = "warehouse_world.sdf"
    robot_sdf = str(description_dir / "models" / "navbot" / "model.sdf")
    robot_urdf = description_dir / "urdf" / "navbot.urdf"
    bridge_config = str(bringup_dir / "config" / "ros_gz_bridge.yaml")
    scan_bridge_config = str(bringup_dir / "config" / "ros_gz_scan_bridge.yaml")
    robot_description = robot_urdf.read_text(encoding="utf-8")

    # Set up Gazebo Resource Path so it can find our custom models and worlds
    existing_resource_path = os.environ.get("GZ_SIM_RESOURCE_PATH", "")
    resource_paths = [
        str(bringup_dir / "worlds"),
        str(description_dir / "models"),
        str(description_dir),
        str(bringup_dir),
    ]
    if existing_resource_path:
        resource_paths.append(existing_resource_path)

    # Launch Gazebo without shell interpolation so workspaces with spaces in
    # their path still work. Starting server and GUI separately avoids a startup
    # race seen in some Wayland/Distrobox sessions.
    gazebo_server = ExecuteProcess(
        cmd=["gz", "sim", "-s", "-r", "-v", "3", world, "--force-version", "8"],
        name="gazebo_server",
        output="screen",
    )

    gazebo_gui = TimerAction(
        period=2.0,
        actions=[
            ExecuteProcess(
                cmd=["gz", "sim", "-g", "-v", "3", "--force-version", "8"],
                name="gazebo_gui",
                output="screen",
                condition=IfCondition(gui),
            )
        ],
    )

    spawn_robot = TimerAction(
        period=2.0,
        actions=[
            Node(
                package="ros_gz_sim",
                executable="create",
                name="spawn_navbot",
                output="screen",
                arguments=[
                    "-file",
                    robot_sdf,
                    "-name",
                    robot_name,
                    "-x",
                    "-4.0",
                    "-y",
                    "-3.0",
                    "-z",
                    "0.02",
                    "-Y",
                    "0.0",
                ],
            )
        ],
    )

    bridge = Node(
        package="ros_gz_bridge",
        executable="parameter_bridge",
        name="ros_gz_bridge",
        output="screen",
        arguments=["--ros-args", "-p", f"config_file:={bridge_config}"],
        parameters=[{"use_sim_time": use_sim_time}],
    )

    gazebo_scan_bridge = Node(
        package="ros_gz_bridge",
        executable="parameter_bridge",
        name="ros_gz_scan_bridge",
        output="screen",
        arguments=["--ros-args", "-p", f"config_file:={scan_bridge_config}"],
        parameters=[{"use_sim_time": use_sim_time}],
        condition=UnlessCondition(use_synthetic_scan),
    )

    scan_frame_republisher = Node(
        package="navbot_mission",
        executable="scan_frame_republisher",
        name="scan_frame_republisher",
        output="screen",
        parameters=[{"use_sim_time": use_sim_time}],
        condition=UnlessCondition(use_synthetic_scan),
    )

    robot_state_publisher = Node(
        package="robot_state_publisher",
        executable="robot_state_publisher",
        name="robot_state_publisher",
        output="screen",
        parameters=[
            {
                "robot_description": robot_description,
                "use_sim_time": use_sim_time,
            }
        ],
    )

    synthetic_scan = Node(
        package="navbot_mission",
        executable="synthetic_scan_publisher",
        name="synthetic_scan_publisher",
        output="screen",
        parameters=[{"use_sim_time": use_sim_time}],
        condition=IfCondition(use_synthetic_scan),
    )

    return LaunchDescription(
        [
            DeclareLaunchArgument("world", default_value=default_world),
            DeclareLaunchArgument("robot_name", default_value="navbot"),
            DeclareLaunchArgument("use_sim_time", default_value="true"),
            DeclareLaunchArgument("gui", default_value="true"),
            DeclareLaunchArgument("use_synthetic_scan", default_value="true"),
            SetEnvironmentVariable("GZ_SIM_RESOURCE_PATH", os.pathsep.join(resource_paths)),
            SetEnvironmentVariable("GZ_IP", "127.0.0.1"),
            gazebo_server,
            gazebo_gui,
            robot_state_publisher,
            synthetic_scan,
            spawn_robot,
            bridge,
            gazebo_scan_bridge,
            scan_frame_republisher,
        ]
    )
