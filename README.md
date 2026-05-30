# ROS 2 NavBot Simulation

![ROS 2](https://img.shields.io/badge/ROS_2-Jazzy-22314E?style=for-the-badge&logo=ros&logoColor=white)
![Gazebo](https://img.shields.io/badge/Gazebo-Harmonic-FF6600?style=for-the-badge&logo=gazebo&logoColor=white)
![Ubuntu](https://img.shields.io/badge/Ubuntu-24.04-E95420?style=for-the-badge&logo=ubuntu&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-blue.svg?style=for-the-badge)

This is a ROS 2 Jazzy simulation where a differential-drive robot navigates a warehouse environment using Gazebo Harmonic, RViz2, and Nav2.

Built this to show a working robotics stack without hiding the tradeoffs. The project uses a custom diff-drive robot, a static warehouse map, Nav2 planning/control, and a Python mission node that sends goals and logs the run.

---

## Demonstration

### Autonomous Navigation
The robot executes a multi-goal mission across the warehouse floor.

![NavBot Demo](docs/screenshots/demo.gif)

### RViz Planning View
RViz shows the static map, robot model, laser scan, costmaps, active goal, and planned path.

![RViz path planning](docs/screenshots/rviz_path_planning.png)

### Mission Execution Logging
Terminal output showing the successful execution and logging of a sequence of goals.

![Mission Complete](docs/screenshots/mission_complete.png)

---

## What This Demonstrates

I designed this project to show how the main pieces of a ROS 2 navigation stack fit together:

- **ROS 2 Package Architecture**: Separated the logic into distinct packages (`bringup`, `description`, `mission`) using colcon build patterns.
- **Simulation Integration**: Uses Gazebo Harmonic (modern Gazebo) and connects to ROS via `ros_gz_sim` and `ros_gz_bridge`.
- **Differential Drive Kinematics**: The robot uses custom URDF and SDF models instead of depending on TurtleBot3 simulator packages.
- **Nav2 Stack**: The navigation is configured with AMCL localization, a static map, layered costmaps, global planning (NavFn), and local control (DWB).
- **Mission Control**: A Python mission node sends `NavigateToPose` goals and logs timing, distance travelled, and path efficiency from `/odom`.

---

## Tech Stack & Engineering Decisions

### Core Technologies
- **OS**: Ubuntu 24.04
- **Middleware**: ROS 2 Jazzy
- **Simulation**: Gazebo Harmonic
- **Navigation**: Nav2 stack
- **Visualization**: RViz2
- **Language**: Python 3 / Bash / C++ (via ROS 2 binaries)

### Engineering Decisions
1. **Custom Robot Definition**: The robot lives in `navbot_description`, with matching URDF for RViz and SDF for Gazebo.
2. **Static Map + AMCL**: The demo uses a known warehouse map and AMCL localization. That keeps the run repeatable while still using the normal Nav2 `map -> odom -> base_footprint` localization flow.
3. **Selectable Laser Source**: By default, Gazebo's simulated lidar feeds AMCL and the Nav2 costmaps. If your graphics stack breaks Gazebo ray sensors, you can switch to the synthetic scan fallback with `use_synthetic_scan:=true`.

---

## System Architecture

Gazebo runs the physics engine and broadcasts odometry and TF data through the ROS bridge. AMCL estimates the robot pose against the static map using odometry and `/scan`, then Nav2 uses that estimate to generate the velocity commands (`/cmd_vel`) that drive the robot.

```mermaid
%%{init: {"theme": "base", "themeVariables": {"fontFamily": "Arial, sans-serif", "primaryTextColor": "#111827", "lineColor": "#475569", "clusterBkg": "#f8fafc", "clusterBorder": "#94a3b8", "edgeLabelBackground": "#ffffff"}}}%%
flowchart LR
    subgraph "Gazebo Environment"
        A[Physics Simulation] 
        I[Diff Drive Plugin]
    end

    subgraph "ROS 2 Core"
        C[Topics: /odom, /tf]
        L[Gazebo Lidar /scan]
        D[Static Map Node]
        M[AMCL Localization]
    end

    subgraph "Nav2 Stack"
        E[Costmap 2D]
        F[Global Planner]
        G[Local Controller]
    end
    
    subgraph "Mission Control"
        J[Mission Python Node]
        K[NavigateToPose Action]
    end

    A -->|State| I
    I -->|ros_gz_bridge| C
    C --> M
    L --> M
    D --> M
    M --> E
    L --> E
    D --> E
    E --> F
    F --> G
    G -->|cmd_vel| I
    J -->|Sends Goal| K
    K --> F
    C -->|odom metrics| J

    classDef gazebo fill:#fff3e0,stroke:#f97316,stroke-width:2px,color:#111827;
    classDef ros fill:#e0f2fe,stroke:#0284c7,stroke-width:2px,color:#111827;
    classDef nav fill:#dcfce7,stroke:#16a34a,stroke-width:2px,color:#111827;
    classDef control fill:#ede9fe,stroke:#7c3aed,stroke-width:2px,color:#111827;

    class A,I gazebo;
    class C,L,D,M ros;
    class E,F,G nav;
    class J,K control;
```

---

## Repository Layout

```text
ros2-navbot-sim/
├── docs/                      # Screenshots, gifs, and architectural documentation
├── scripts/                   # Bash utilities for setup and execution
└── src/
    ├── navbot_bringup/        # High-level launch files, Nav2 config, maps, and Gazebo worlds
    ├── navbot_description/    # Robot URDF, SDF, meshes, and kinematic models
    └── navbot_mission/        # Python ROS 2 nodes for mission orchestration and metrics logging
```

---

## Quick Start

### 1. Environment Setup

Run this on **Ubuntu 24.04** with the ROS 2 Jazzy apt repository configured:

```bash
cd ros2-navbot-sim
./scripts/setup_ubuntu_24_04.sh
```
*Note: If ROS 2 Jazzy isn't installed yet, install it first, then run this setup script to fetch the dependencies and build the workspace.*

### 2. Launch the Demo

You can launch Gazebo, RViz, the ROS bridges, Nav2, and the custom mission node with a single command:

```bash
cd ros2-navbot-sim
./scripts/run_demo.sh
```

Useful launch options:

```bash
# Run without the Gazebo GUI. Handy on Wayland/NVIDIA setups where Gazebo renders black.
./scripts/run_demo.sh gui:=false

# Use the synthetic scan fallback if Gazebo's lidar sensor does not publish on your machine.
./scripts/run_demo.sh use_synthetic_scan:=true

# Launch RViz/Nav2 only, without starting the mission automatically.
./scripts/run_demo.sh start_mission:=false
```

### 3. Observe the Output

Once everything is up, the mission node will output the progress of the multi-goal navigation directly to the terminal. You should see logs like this:

```text
[multi_goal_nav] Publishing initial pose: x=-4.00 y=-3.00 yaw=0.00
[multi_goal_nav] Waiting for bt_navigator lifecycle state ACTIVE...
[multi_goal_nav] Goal 1/3 west_staging: x=-2.40 y=-3.00 yaw=0.00
[multi_goal_nav] Goal west_staging status: distance_remaining=0.50m navigation_time=5.0s recoveries=0
[multi_goal_nav] Goal west_staging succeeded in 6.3s; traveled=1.42m straight_line=1.42m efficiency=100.0%
...
[multi_goal_nav] Mission complete: 3/3 goals reached in 26.2s; traveled=6.21m efficiency=100.0%
[multi_goal_nav] Wrote mission log: logs/mission_2026-05-22T10-42-10.json
```

The JSON log keeps the same metrics per goal and adds a mission summary, which makes it easier to compare navigation runs after changing planner or controller parameters.

## More Notes

- [Architecture notes](docs/architecture.md)
- [Engineering notes](docs/engineering_notes.md)
