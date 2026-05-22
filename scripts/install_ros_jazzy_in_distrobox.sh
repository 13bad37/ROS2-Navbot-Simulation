#!/usr/bin/env bash
set -euo pipefail

if [[ "${container:-}" != "podman" && "${DISTROBOX_ENTER_PATH:-}" == "" ]]; then
  echo "Run this inside the Ubuntu 24.04 Distrobox container." >&2
  exit 1
fi

if [[ ! -f /etc/os-release ]]; then
  echo "Cannot detect the container operating system." >&2
  exit 1
fi

. /etc/os-release
if [[ "${ID:-}" != "ubuntu" || "${VERSION_CODENAME:-}" != "noble" ]]; then
  echo "Expected Ubuntu 24.04 noble, got ${PRETTY_NAME:-unknown}." >&2
  exit 1
fi

sudo apt update
sudo apt install -y \
  curl \
  git \
  gnupg \
  lsb-release \
  locales \
  python3-yaml \
  software-properties-common

sudo locale-gen en_US en_US.UTF-8
sudo update-locale LC_ALL=en_US.UTF-8 LANG=en_US.UTF-8
export LANG=en_US.UTF-8

sudo add-apt-repository -y universe
sudo apt update

ROS_APT_SOURCE_VERSION="$(
  curl -s https://api.github.com/repos/ros-infrastructure/ros-apt-source/releases/latest \
    | grep -F "tag_name" \
    | awk -F'"' '{print $4}'
)"

if [[ -z "$ROS_APT_SOURCE_VERSION" ]]; then
  echo "Could not determine latest ros-apt-source release." >&2
  exit 1
fi

curl -L -o /tmp/ros2-apt-source.deb \
  "https://github.com/ros-infrastructure/ros-apt-source/releases/download/${ROS_APT_SOURCE_VERSION}/ros2-apt-source_${ROS_APT_SOURCE_VERSION}.${VERSION_CODENAME}_all.deb"

sudo dpkg -i /tmp/ros2-apt-source.deb
sudo apt update

sudo apt install -y \
  python3-colcon-common-extensions \
  python3-pytest \
  python3-rosdep \
  ros-jazzy-ament-cmake-pytest \
  ros-dev-tools \
  ros-jazzy-desktop \
  ros-jazzy-navigation2 \
  ros-jazzy-nav2-bringup \
  ros-jazzy-robot-state-publisher \
  ros-jazzy-ros-gz \
  ros-jazzy-ros-gz-bridge \
  ros-jazzy-ros-gz-sim \
  ros-jazzy-rviz2 \
  ros-jazzy-tf2-ros

sudo rosdep init 2>/dev/null || true
rosdep update

if ! grep -q "source /opt/ros/jazzy/setup.bash" "$HOME/.bashrc"; then
  echo "source /opt/ros/jazzy/setup.bash" >> "$HOME/.bashrc"
fi

set +u
source /opt/ros/jazzy/setup.bash
set -u
ros2 --version
colcon version-check || true

echo "ROS 2 Jazzy install complete."
