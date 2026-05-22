#!/usr/bin/env bash
set -euo pipefail

# Captures portfolio screenshots and short clips from a running desktop demo.
#
# The script does not generate placeholder media. If Gazebo, RViz, and the
# mission terminal are not visible, stop and run ./scripts/run_demo.sh first.
# Usage:
#   ./scripts/record_demo.sh screenshots
#   ./scripts/record_demo.sh gif
#   ./scripts/record_demo.sh video

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
OUT_DIR="$ROOT_DIR/docs/screenshots"
MODE="${1:-help}"

mkdir -p "$OUT_DIR"

case "$MODE" in
  screenshots)
    echo "Capturing screenshots into $OUT_DIR"
    if command -v gnome-screenshot >/dev/null 2>&1; then
      echo "Select the Gazebo window, then press Enter."
      read -r
      gnome-screenshot -w -f "$OUT_DIR/gazebo_world.png"
      echo "Select the RViz window, then press Enter."
      read -r
      gnome-screenshot -w -f "$OUT_DIR/rviz_path_planning.png"
      echo "Select the mission terminal, then press Enter."
      read -r
      gnome-screenshot -w -f "$OUT_DIR/mission_complete.png"
    elif command -v grim >/dev/null 2>&1; then
      if command -v slurp >/dev/null 2>&1; then
        echo "Select the Gazebo window or region."
        grim -g "$(slurp)" "$OUT_DIR/gazebo_world.png"
        echo "Select the RViz window or region."
        grim -g "$(slurp)" "$OUT_DIR/rviz_path_planning.png"
        echo "Select the mission terminal window or region."
        grim -g "$(slurp)" "$OUT_DIR/mission_complete.png"
      else
        echo "Using grim for full-screen Wayland screenshots."
        echo "Move Gazebo into view, then press Enter."
        read -r
        grim "$OUT_DIR/gazebo_world.png"
        echo "Move RViz into view, then press Enter."
        read -r
        grim "$OUT_DIR/rviz_path_planning.png"
        echo "Move the mission terminal into view, then press Enter."
        read -r
        grim "$OUT_DIR/mission_complete.png"
      fi
    else
      echo "Install gnome-screenshot or grim, then rerun this command." >&2
      exit 1
    fi
    ;;
  gif)
    echo "Recording a short GIF into $OUT_DIR/demo.gif"
    if command -v wf-recorder >/dev/null 2>&1 && [[ -n "${WAYLAND_DISPLAY:-}" ]]; then
      tmp_video="$OUT_DIR/demo.mp4"
      echo "Using wf-recorder on WAYLAND_DISPLAY=$WAYLAND_DISPLAY for 15 seconds."
      if command -v slurp >/dev/null 2>&1; then
        region="$(slurp)"
        timeout 15s wf-recorder -g "$region" -f "$tmp_video" || true
      else
        timeout 15s wf-recorder -f "$tmp_video" || true
      fi
      if ! command -v ffmpeg >/dev/null 2>&1; then
        echo "Recorded $tmp_video, but ffmpeg is required to convert it to demo.gif." >&2
        exit 1
      fi
      ffmpeg -y -i "$tmp_video" -vf "fps=12,scale=960:-1:flags=lanczos" "$OUT_DIR/demo.gif"
    elif ! command -v ffmpeg >/dev/null 2>&1; then
      echo "ffmpeg is required for GIF recording." >&2
      exit 1
    elif [[ -z "${DISPLAY:-}" ]]; then
      echo "DISPLAY is not set. GIF recording through x11grab requires an X11 session." >&2
      echo "On Hyprland, install wf-recorder and slurp for native Wayland recording." >&2
      exit 1
    else
      echo "Recording 15 seconds from DISPLAY=$DISPLAY at 1280x720."
      ffmpeg -y -video_size 1280x720 -framerate 12 -f x11grab -i "$DISPLAY" -t 15 \
        -vf "fps=12,scale=960:-1:flags=lanczos" "$OUT_DIR/demo.gif"
    fi
    ;;
  video)
    echo "Recording a short video into $OUT_DIR/demo.mp4"
    if ! command -v wf-recorder >/dev/null 2>&1; then
      echo "wf-recorder is required for Wayland video capture." >&2
      exit 1
    fi
    if [[ -z "${WAYLAND_DISPLAY:-}" ]]; then
      echo "WAYLAND_DISPLAY is not set. This mode is for Wayland/Hyprland sessions." >&2
      exit 1
    fi
    if command -v slurp >/dev/null 2>&1; then
      region="$(slurp)"
      timeout 15s wf-recorder -g "$region" -f "$OUT_DIR/demo.mp4" || true
    else
      timeout 15s wf-recorder -f "$OUT_DIR/demo.mp4" || true
    fi
    ;;
  *)
    echo "Usage: $0 screenshots|gif|video"
    echo
    echo "Start ./scripts/run_demo.sh first, then arrange Gazebo, RViz, and the terminal."
    ;;
esac
