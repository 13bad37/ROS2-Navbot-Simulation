#!/usr/bin/env bash
set -euo pipefail

# Builds the workspace, sources it, then launches Gazebo, RViz, Nav2, and the mission node.
# Extra ROS launch arguments are forwarded, e.g. gui:=false or start_mission:=false.

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

if [[ ! -f /opt/ros/jazzy/setup.bash ]]; then
  echo "ROS 2 Jazzy was not found at /opt/ros/jazzy/setup.bash." >&2
  echo "Install ROS 2 Jazzy or run scripts/setup_ubuntu_24_04.sh first." >&2
  exit 1
fi

set +u
source /opt/ros/jazzy/setup.bash
set -u

if [[ "${ROS_DISTRO:-}" != "jazzy" ]]; then
  echo "Expected ROS_DISTRO=jazzy, got ROS_DISTRO=${ROS_DISTRO:-unset}." >&2
  exit 1
fi

# RViz is more reliable through XWayland from Arch/Hyprland Distrobox sessions.
# RViz gets software OpenGL from the launch file; Gazebo should keep hardware GL.
if [[ -n "${WAYLAND_DISPLAY:-}" && -n "${DISPLAY:-}" ]]; then
  if [[ -z "${QT_QPA_PLATFORM:-}" || "${QT_QPA_PLATFORM}" == *wayland* ]]; then
    export QT_QPA_PLATFORM=xcb
  fi
fi

cd "$ROOT_DIR"

if [[ ! -f install/setup.bash ]]; then
  colcon build --symlink-install
else
  colcon build --symlink-install
fi

set +u
source install/setup.bash
set -u
mkdir -p logs

exec ros2 launch navbot_bringup demo.launch.py "$@"
