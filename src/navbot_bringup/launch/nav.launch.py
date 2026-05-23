from pathlib import Path

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.conditions import IfCondition
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    """
    Launch the Nav2 navigation stack and RViz.

    This launch file configures and starts the Nav2 nodes necessary for
    autonomous navigation. It brings up:
    1. Map Server and AMCL localization for the fixed static map.
    2. Nav2 Controller, Planner, Smoother, Behavior, and Waypoint Follower servers.
    3. Lifecycle managers to transition Nav2 nodes to the ACTIVE state.
    4. RViz2 for visualization.
    """
    bringup_dir = Path(get_package_share_directory("navbot_bringup"))

    # Launch Arguments
    use_sim_time = LaunchConfiguration("use_sim_time")
    map_file = LaunchConfiguration("map")
    params_file = LaunchConfiguration("params_file")
    rviz = LaunchConfiguration("rviz")
    rviz_config = LaunchConfiguration("rviz_config")

    remappings = [("/tf", "tf"), ("/tf_static", "tf_static")]
    nav_nodes = [
        "controller_server",
        "smoother_server",
        "planner_server",
        "behavior_server",
        "bt_navigator",
        "waypoint_follower",
        "velocity_smoother",
    ]

    common_params = [params_file, {"use_sim_time": use_sim_time}]

    map_server = Node(
        package="nav2_map_server",
        executable="map_server",
        name="map_server",
        output="screen",
        parameters=[params_file, {"use_sim_time": use_sim_time, "yaml_filename": map_file}],
        remappings=remappings,
    )

    amcl = Node(
        package="nav2_amcl",
        executable="amcl",
        name="amcl",
        output="screen",
        parameters=[params_file, {"use_sim_time": use_sim_time}],
        remappings=remappings,
    )

    map_lifecycle = Node(
        package="nav2_lifecycle_manager",
        executable="lifecycle_manager",
        name="lifecycle_manager_localization",
        output="screen",
        parameters=[
            {
                "use_sim_time": use_sim_time,
                "autostart": True,
                "node_names": ["map_server", "amcl"],
            }
        ],
    )

    controller_server = Node(
        package="nav2_controller",
        executable="controller_server",
        output="screen",
        parameters=common_params,
        remappings=remappings + [("cmd_vel", "cmd_vel_nav")],
    )

    smoother_server = Node(
        package="nav2_smoother",
        executable="smoother_server",
        name="smoother_server",
        output="screen",
        parameters=common_params,
        remappings=remappings,
    )

    planner_server = Node(
        package="nav2_planner",
        executable="planner_server",
        name="planner_server",
        output="screen",
        parameters=common_params,
        remappings=remappings,
    )

    behavior_server = Node(
        package="nav2_behaviors",
        executable="behavior_server",
        name="behavior_server",
        output="screen",
        parameters=common_params,
        remappings=remappings + [("cmd_vel", "cmd_vel_nav")],
    )

    bt_navigator = Node(
        package="nav2_bt_navigator",
        executable="bt_navigator",
        name="bt_navigator",
        output="screen",
        parameters=common_params,
        remappings=remappings,
    )

    waypoint_follower = Node(
        package="nav2_waypoint_follower",
        executable="waypoint_follower",
        name="waypoint_follower",
        output="screen",
        parameters=common_params,
        remappings=remappings,
    )

    velocity_smoother = Node(
        package="nav2_velocity_smoother",
        executable="velocity_smoother",
        name="velocity_smoother",
        output="screen",
        parameters=common_params,
        remappings=remappings
        + [
            ("cmd_vel", "cmd_vel_nav"),
            ("cmd_vel_smoothed", "cmd_vel"),
        ],
    )

    navigation_lifecycle = Node(
        package="nav2_lifecycle_manager",
        executable="lifecycle_manager",
        name="lifecycle_manager_navigation",
        output="screen",
        parameters=[
            {
                "use_sim_time": use_sim_time,
                "autostart": True,
                "node_names": nav_nodes,
            }
        ],
    )

    rviz_node = Node(
        package="rviz2",
        executable="rviz2",
        name="rviz2",
        output="screen",
        condition=IfCondition(rviz),
        arguments=["-d", rviz_config],
        parameters=[{"use_sim_time": use_sim_time}],
        additional_env={"LIBGL_ALWAYS_SOFTWARE": "1"},
    )

    return LaunchDescription(
        [
            DeclareLaunchArgument("use_sim_time", default_value="true"),
            DeclareLaunchArgument("rviz", default_value="true"),
            DeclareLaunchArgument(
                "map",
                default_value=str(bringup_dir / "maps" / "warehouse_map.yaml"),
            ),
            DeclareLaunchArgument(
                "params_file",
                default_value=str(bringup_dir / "config" / "nav2_params.yaml"),
            ),
            DeclareLaunchArgument(
                "rviz_config",
                default_value=str(bringup_dir / "config" / "rviz_config.rviz"),
            ),
            map_server,
            amcl,
            map_lifecycle,
            controller_server,
            smoother_server,
            planner_server,
            behavior_server,
            bt_navigator,
            waypoint_follower,
            velocity_smoother,
            navigation_lifecycle,
            rviz_node,
        ]
    )
