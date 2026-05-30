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

By default, the Gazebo lidar sensor publishes `/gz_scan`; `ros_gz_scan_bridge` exposes it as `/gz_scan_raw`, then `scan_frame_republisher.py` republishes it as `/scan` with the `lidar_link` frame. Launch with `use_synthetic_scan:=true` to use the synthetic scan fallback on machines where Gazebo ray sensors are unreliable.

`robot_state_publisher` publishes the robot's fixed transforms from the URDF, including `base_footprint`, `base_link`, wheel links, and `lidar_link`.

## Navigation Stack

Nav2 uses a static map and AMCL localization. AMCL consumes `/odom`, `/scan`, and `/map`, then publishes the `map -> odom` transform used by the global costmap. The global costmap uses the static map and inflation; the local costmap uses scan observations in the odom frame for close-range obstacle handling.

## Mission Execution

`navbot_mission/multi_goal_nav.py` loads an initial pose and a list of goals from `config/goals.yaml`. It waits for AMCL to subscribe to `/initialpose`, publishes the initial pose, waits for Nav2, sends each goal, prints progress, and records a JSON mission summary under `logs/`.

The mission node also subscribes to `/odom`. `odom_distance_tracker.py` integrates the distance between consecutive odometry samples and compares that travelled distance with each leg's straight-line displacement. The resulting efficiency metrics are useful when tuning planners and controllers.

## Frames

- `map`: static map frame, parent of `odom` from AMCL.
- `odom`: continuous odometry frame, parent of `base_footprint` from Gazebo diff-drive.
- `base_footprint`: planar robot base frame for Nav2.
- `base_link`: robot body frame.
- `lidar_link`: laser scan frame.
