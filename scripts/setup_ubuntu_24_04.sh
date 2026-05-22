#!/usr/bin/env bash
set -euo pipefail

# Installs this workspace's ROS dependencies and builds the packages.
# Keep ROS installation itself separate so failures are easier to diagnose.

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

if [[ "$(lsb_release -cs)" != "noble" ]]; then
  echo "This setup script targets Ubuntu 24.04 (noble)." >&2
  exit 1
fi

if [[ ! -f /opt/ros/jazzy/setup.bash ]]; then
  echo "ROS 2 Jazzy was not found at /opt/ros/jazzy." >&2
  echo "Install ROS 2 Jazzy first, then rerun this script." >&2
  exit 1
fi

set +u
source /opt/ros/jazzy/setup.bash
set -u

if [[ "${ROS_DISTRO:-}" != "jazzy" ]]; then
  echo "Expected ROS_DISTRO=jazzy, got ROS_DISTRO=${ROS_DISTRO:-unset}." >&2
  exit 1
fi

sudo apt update
sudo apt install -y \
  python3-colcon-common-extensions \
  python3-rosdep \
  python3-yaml \
  ros-jazzy-ament-cmake-pytest \
  ros-jazzy-navigation2 \
  ros-jazzy-nav2-bringup \
  ros-jazzy-ros-gz \
  ros-jazzy-ros-gz-bridge \
  ros-jazzy-ros-gz-sim \
  ros-jazzy-rviz2 \
  ros-jazzy-robot-state-publisher \
  ros-jazzy-tf2-ros

if ! rosdep --version >/dev/null 2>&1; then
  echo "rosdep is not available after installation." >&2
  exit 1
fi

if [[ ! -d /etc/ros/rosdep/sources.list.d ]]; then
  sudo rosdep init
fi

rosdep update

cd "$ROOT_DIR"
rosdep install --from-paths src --ignore-src --skip-keys ament_python -r -y
colcon build --symlink-install

echo
echo "Setup complete."
echo "Run: source install/setup.bash"
echo "Then: ./scripts/run_demo.sh"
