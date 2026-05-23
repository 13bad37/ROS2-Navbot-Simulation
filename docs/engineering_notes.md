# Engineering Notes

## Why Static Map Navigation

This project uses a static map with AMCL localization. That is simpler than SLAM, but still follows the standard Nav2 pattern: odometry provides short-term motion, AMCL estimates `map -> odom` from the map and scan data, and Nav2 plans in the `map` frame. The focus is on launching a complete stack, planning paths, driving the robot, and logging a mission.

## Laser Scan Strategy

The default scan source is Gazebo's simulated lidar. It publishes `/gz_scan`, `ros_gz_scan_bridge` exposes it as `/gz_scan_raw`, and `scan_frame_republisher.py` republishes it as `/scan` with the `lidar_link` frame that Nav2 expects. That gives AMCL actual range observations instead of a constant synthetic scan.

The synthetic scan path is still available for machines where Gazebo ray sensors fail:

```bash
./scripts/run_demo.sh use_synthetic_scan:=true
```

The synthetic fallback publishes a clean 360 degree `LaserScan`; it is useful for testing Nav2 startup, but it gives AMCL much less information than real simulated lidar.

## Why A Custom Robot

TurtleBot3 is convenient, but simulator integration can shift across ROS/Gazebo versions. The custom robot keeps the project self-contained and makes the URDF/SDF, TF frames, wheel geometry, and diff-drive plugin setup visible in the repo.

## Waypoint Goals

The mission goals are treated as position waypoints. The yaw tolerance is intentionally loose because this demo is about localization, path planning, and reaching stops, not precision docking. That avoids wasting time on in-place rotations near obstacles after the robot has already reached the waypoint.

## What This Demo Does Not Claim

This is not a production autonomous robot stack. It does not include SLAM, recovery tuning for large dynamic scenes, perception pipelines, or hardware drivers. The default path uses Gazebo lidar, while the synthetic scan path is a fallback for difficult desktop/container graphics setups.
