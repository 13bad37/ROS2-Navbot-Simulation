# Engineering Notes

## Why Static Map Navigation

This project uses a static map and a fixed `map -> odom` transform. That is simpler than SLAM or AMCL, but it is a good fit for a portfolio demo because it makes the navigation behavior repeatable. The focus is on launching a complete stack, planning paths, driving the robot, and logging a mission.

## Laser Scan Strategy

The default scan source is `synthetic_scan_publisher.py`. It publishes a clean 360 degree `LaserScan` from `lidar_link`, which keeps Nav2 stable on desktops where Gazebo sensor rendering can fail. This means the default demo avoids mapped obstacles using the static map, not live obstacle discovery from Gazebo.

The robot SDF also includes a Gazebo lidar sensor. The optional path bridges Gazebo's `/gz_scan` topic into ROS as `/gz_scan_raw`, then republishes it as `/scan` with the `lidar_link` frame that Nav2 expects. To try it, run:

```bash
./scripts/run_demo.sh use_synthetic_scan:=false
```

If your Gazebo viewport or lidar rendering fails, switch back to the default synthetic scan path.

## Why A Custom Robot

TurtleBot3 is convenient, but simulator integration can shift across ROS/Gazebo versions. The custom robot keeps the project self-contained and makes the URDF/SDF, TF frames, wheel geometry, and diff-drive plugin setup visible in the repo.

## What This Demo Does Not Claim

This is not a production autonomous robot stack. It does not include SLAM, recovery tuning for large dynamic scenes, perception pipelines, or hardware drivers. It is a compact ROS 2/Nav2 simulation that demonstrates the core navigation workflow clearly.
