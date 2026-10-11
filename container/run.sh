#!/usr/bin/env bash
set -euo pipefail

if [ "$#" -lt 1 ]; then
  echo "Usage: $0 /path/to/repo"
  exit 1
fi

REPO_ROOT="$1"
IMAGE_NAME="habit-tracker-check"
CONTAINER_NAME="habit-tracker-check"
PORT="${PORT:-8000}"
DATA_DIR="${DATA_DIR:-/data}"

if ! command -v docker >/dev/null 2>&1; then
  echo "ERROR: docker CLI not found. Install Docker before running this checker."
  exit 127
fi

printf 'Building image %s from %s\n' "$IMAGE_NAME" "$REPO_ROOT"
docker build -t "$IMAGE_NAME" "$REPO_ROOT" >/dev/null

docker rm -f "$CONTAINER_NAME" >/dev/null 2>&1 || true

docker run -d --rm \
  --name "$CONTAINER_NAME" \
  -p "${PORT}:${PORT}" \
  -e PORT="$PORT" \
  -e DATA_DIR="$DATA_DIR" \
  -v "${REPO_ROOT}/data:${DATA_DIR}" \
  "$IMAGE_NAME" >/dev/null

trap 'docker rm -f "$CONTAINER_NAME" >/dev/null 2>&1 || true' EXIT

for _ in $(seq 1 30); do
  if curl -fsS "http://127.0.0.1:${PORT}/health" >/tmp/habit_tracker_health.json 2>/dev/null; then
    cat /tmp/habit_tracker_health.json
    echo
    exit 0
  fi
  sleep 1
done

echo "ERROR: app did not become healthy on port ${PORT}"
exit 1
