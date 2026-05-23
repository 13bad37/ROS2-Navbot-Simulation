# Troubleshooting

## ROS 2 is not found

Run:

```bash
source /opt/ros/jazzy/setup.bash
echo "$ROS_DISTRO"
```

Expected output:

```text
jazzy
```

If `/opt/ros/jazzy` does not exist, install ROS 2 Jazzy first.

## Gazebo starts but the robot does not appear

Check that the description package is built and sourced:

```bash
colcon build --symlink-install
source install/setup.bash
ros2 pkg prefix navbot_description
```

Then check the Gazebo spawn output in the launch terminal.

## Nav2 does not become active

Run:

```bash
ros2 lifecycle nodes
ros2 topic list | grep -E 'scan|odom|tf|map'
```

Expected topics include `/scan`, `/odom`, `/tf`, `/tf_static`, and `/map`.

## RViz shows transform errors

Wait for Gazebo and Nav2 to finish startup. If errors remain, verify:

```bash
ros2 run tf2_ros tf2_echo map odom
ros2 run tf2_ros tf2_echo map base_footprint
ros2 run tf2_ros tf2_echo base_link lidar_link
```

If `map -> odom` is missing, check that `/amcl` is running, `/scan` is publishing, `/odom` is publishing, and the mission node has published `/initialpose`. If `base_link -> lidar_link` is missing, check `robot_state_publisher`.

## The robot does not move

Check that Nav2 is publishing velocity commands and Gazebo is receiving them:

```bash
ros2 topic echo /cmd_vel
ros2 topic echo /odom
```

If `/cmd_vel` publishes but `/odom` does not change, inspect the `ros_gz_bridge` command in `sim.launch.py`.

## `/scan` is missing

The default launch path uses the Gazebo lidar bridge and republishes `/gz_scan_raw` as `/scan`:

```bash
ros2 topic hz /scan
```

If `/scan` is missing, your Gazebo lidar sensor path is not working in that environment. Switch to the fallback:

```bash
./scripts/run_demo.sh use_synthetic_scan:=true
```

## The robot gets stuck near obstacles

The demo uses conservative inflation and a small warehouse. If the robot oscillates, restart the demo and let Nav2 become fully active before the first goal. You can also reduce `inflation_radius` slightly in `src/navbot_bringup/config/nav2_params.yaml`.

## Gazebo GUI opens but the 3D viewport is black

This can happen on Arch/Hyprland when Gazebo Harmonic runs inside an Ubuntu Distrobox with NVIDIA graphics. The Gazebo server can still run correctly while the GUI viewport renders black.

Practical options:

- Run the demo on native Ubuntu 24.04 with ROS 2 Jazzy and Gazebo Harmonic for the cleanest Gazebo screenshot.
- Keep the Distrobox setup for development and use RViz for navigation screenshots.
- Launch without the Gazebo GUI:

```bash
./scripts/run_demo.sh gui:=false
```

- Do not commit a fake `gazebo_world.png`; capture it from an environment where the Gazebo GUI actually renders.

## Screenshots are missing

The repo intentionally avoids fake screenshots. Run the demo until the robot is moving or the mission is complete, then capture real screenshots:

```bash
./scripts/record_demo.sh screenshots
./scripts/record_demo.sh gif
```
