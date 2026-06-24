#!/bin/bash
# Helper script to run the Buildozer Docker image locally and build the APK.
# Usage: ./docker-build.sh
set -euo pipefail
PROJECT_DIR="$(pwd)"
IMAGE="kivy/buildozer:latest"

# Create .buildozer folder if missing for caches
mkdir -p "$PROJECT_DIR/.buildozer"

docker run --rm \
  -e CI=true \
  -v "$PROJECT_DIR":/home/user/project \
  -v "$PROJECT_DIR/.buildozer":/home/user/.buildozer \
  -w /home/user/project \
  "$IMAGE" buildozer android debug

# After run, APK(s) will be written into the repo (search for *.apk)
