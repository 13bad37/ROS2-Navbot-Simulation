from pathlib import Path

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription, TimerAction
from launch.conditions import IfCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    """
    Generate the primary top-level launch description for the NavBot simulation.

    This launch file orchestrates the entire simulation stack by bringing up
    Gazebo (sim.launch.py), the Nav2 stack (nav.launch.py), and finally the
    mission execution node. TimerActions are used to sequence the startup,
    allowing Gazebo and Nav2 to initialize before the mission starts.
    """
    bringup_dir = Path(get_package_share_directory("navbot_bringup"))
    mission_dir = Path(get_package_share_directory("navbot_mission"))

    # Launch Arguments
    use_sim_time = LaunchConfiguration("use_sim_time")
    rviz = LaunchConfiguration("rviz")
    start_mission = LaunchConfiguration("start_mission")
    log_dir = LaunchConfiguration("log_dir")
    gui = LaunchConfiguration("gui")
    use_synthetic_scan = LaunchConfiguration("use_synthetic_scan")

    # 1. Simulation Bringup: Starts Gazebo Harmonic, spawns the robot, and starts ROS bridges.
    sim_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(str(bringup_dir / "launch" / "sim.launch.py")),
        launch_arguments={
            "use_sim_time": use_sim_time,
            "gui": gui,
            "use_synthetic_scan": use_synthetic_scan,
        }.items(),
    )

    nav_launch = TimerAction(
        period=5.0,
        actions=[
            IncludeLaunchDescription(
                PythonLaunchDescriptionSource(str(bringup_dir / "launch" / "nav.launch.py")),
                launch_arguments={
                    "use_sim_time": use_sim_time,
                    "rviz": rviz,
                }.items(),
            )
        ],
    )

    mission_node = TimerAction(
        period=12.0,
        actions=[
            Node(
                package="navbot_mission",
                executable="multi_goal_nav",
                name="multi_goal_nav",
                output="screen",
                condition=IfCondition(start_mission),
                parameters=[
                    {
                        "use_sim_time": use_sim_time,
                        "goals_file": str(mission_dir / "config" / "goals.yaml"),
                        "log_dir": log_dir,
                    }
                ],
            )
        ],
    )

    return LaunchDescription(
        [
            DeclareLaunchArgument("use_sim_time", default_value="true"),
            DeclareLaunchArgument("rviz", default_value="true"),
            DeclareLaunchArgument("start_mission", default_value="true"),
            DeclareLaunchArgument("gui", default_value="true"),
            DeclareLaunchArgument("use_synthetic_scan", default_value="true"),
            DeclareLaunchArgument("log_dir", default_value="logs"),
            sim_launch,
            nav_launch,
            mission_node,
        ]
    )
