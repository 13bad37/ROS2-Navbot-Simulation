# Screenshots

This folder is for screenshots and short clips captured from the running demo.

Recommended files:

- `gazebo_world.png`: Gazebo warehouse view with robot visible. Only add this if Gazebo actually renders in your environment.
- `rviz_path_planning.png`: RViz showing map, costmaps, scan, and planned path.
- `mission_complete.png`: terminal output showing mission completion.
- `demo.gif`: short clip of the robot moving between goals.
- `demo.mp4`: optional raw local video capture. This file is ignored by git by default.

Use:

```bash
./scripts/record_demo.sh screenshots
./scripts/record_demo.sh gif
./scripts/record_demo.sh video
```

Before committing media, check that `logs/` contains a mission JSON file with `completed_goals` matching the goal count in `src/navbot_mission/config/goals.yaml`.
