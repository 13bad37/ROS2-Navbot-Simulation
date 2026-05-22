# Architecture

`ros2-navbot-sim` is split into three ROS 2 packages:

- `navbot_description`: robot model files for RViz and Gazebo.
- `navbot_bringup`: launch files, Nav2 configuration, RViz configuration, map, and world.
- `navbot_mission`: Python mission node, goal loading, and metrics logging.

## Data Flow

Gazebo owns the simulated world and robot physics. The robot SDF includes a differential-drive system. `ros_gz_bridge` exposes the simulation topics to ROS 2:

- `/cmd_vel`: ROS 2 to Gazebo, consumed by the diff-drive plugin.
- `/odom`: Gazebo to ROS 2, consumed by Nav2 and RViz.
- `/tf`: Gazebo to ROS 2 for odom to base transform.
- `/clock`: Gazebo to ROS 2 for simulation time.

By default, `navbot_mission/synthetic_scan_publisher.py` publishes `/scan` from `lidar_link`. This keeps the demo stable on machines where Gazebo's lidar rendering is unreliable. The robot SDF also includes a Gazebo lidar sensor that publishes `/gz_scan`; launch with `use_synthetic_scan:=false` to bridge it into ROS as `/gz_scan_raw`, then republish it as `/scan` with the `lidar_link` frame.

`robot_state_publisher` publishes the robot's fixed transforms from the URDF, including `base_footprint`, `base_link`, wheel links, and `lidar_link`.

## Navigation Stack

Nav2 uses a static map and a fixed `map -> odom` transform. The global costmap uses the static map plus scan observations. The local costmap uses scan observations in the odom frame. With the default synthetic scan, the map is the source of obstacle layout, so the demo shows repeatable map-based planning. With `use_synthetic_scan:=false`, Gazebo's lidar path can also feed observed obstacles into the costmaps.

## Mission Execution

`navbot_mission/multi_goal_nav.py` loads an initial pose and a list of goals from `config/goals.yaml`. It waits for the Nav2 `NavigateToPose` action server, publishes the initial pose, sends each goal, prints progress, and records a JSON mission summary under `logs/`.

## Frames

- `map`: static map frame, parent of `odom` from `static_transform_publisher`.
- `odom`: continuous odometry frame, parent of `base_footprint` from Gazebo diff-drive.
- `base_footprint`: planar robot base frame for Nav2.
- `base_link`: robot body frame.
- `lidar_link`: laser scan frame.
