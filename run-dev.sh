#!/usr/bin/env bash
set -euo pipefail

# MONITOR dev runner: raises Docker services (Neo4j), API server (uvicorn), and Streamlit UI.
# Usage:
#   ./run-dev.sh up       # start db + api + ui
#   ./run-dev.sh down     # stop db and background processes
#   ./run-dev.sh status   # show ports and processes
#   ./run-dev.sh logs     # tail uvicorn and streamlit logs
#
# Notes:
# - Requires Python 3.11+ and Docker installed.
# - Creates/uses .venv in repo root.
# - Binds: API http://localhost:8000, Streamlit http://localhost:8501, Neo4j http://localhost:7474

ROOT_DIR="$(cd "$(dirname "$0")" && pwd)"
VENV_DIR="$ROOT_DIR/.venv"
LOG_DIR="$ROOT_DIR/.logs"
UVICORN_LOG="$LOG_DIR/uvicorn.log"
STREAMLIT_LOG="$LOG_DIR/streamlit.log"

mkdir -p "$LOG_DIR"

ensure_venv() {
  if [[ ! -d "$VENV_DIR" ]]; then
    echo "[setup] Creating venv at $VENV_DIR"
    python3 -m venv "$VENV_DIR"
  fi
  # shellcheck disable=SC1091
  source "$VENV_DIR/bin/activate"
  python -m pip install --upgrade pip >/dev/null
  if [[ -f "$ROOT_DIR/requirements.txt" ]]; then
    echo "[setup] Installing requirements"
    pip install -r "$ROOT_DIR/requirements.txt" >/dev/null
  fi
}

start_docker() {
  if command -v docker >/dev/null 2>&1; then
    echo "[docker] Compose up (detached)"
    docker compose -f "$ROOT_DIR/docker-compose.yml" up -d
  else
    echo "[docker] Docker not found; skipping"
  fi
}

start_api() {
  echo "[api] Starting uvicorn on :8000"
  # shellcheck disable=SC2086
  nohup uvicorn core.interfaces.api_interface:app \
    --host 0.0.0.0 --port 8000 --reload \
    >"$UVICORN_LOG" 2>&1 &
  echo $! > "$LOG_DIR/uvicorn.pid"
}

start_ui() {
  echo "[ui] Starting Streamlit on :8501"
  nohup streamlit run "$ROOT_DIR/frontend/Chat.py" \
    --server.address=0.0.0.0 --server.port=8501 \
    >"$STREAMLIT_LOG" 2>&1 &
  echo $! > "$LOG_DIR/streamlit.pid"
}

stop_bg() {
  for name in uvicorn streamlit; do
    PID_FILE="$LOG_DIR/$name.pid"
    if [[ -f "$PID_FILE" ]]; then
      PID=$(cat "$PID_FILE" || true)
      if [[ -n "${PID:-}" ]] && kill -0 "$PID" 2>/dev/null; then
        echo "[stop] Killing $name (pid $PID)"
        kill "$PID" || true
      fi
      rm -f "$PID_FILE"
    fi
  done
}

status() {
  echo "[status] Ports in use (8000, 8501, 7474, 7687):"
  command -v lsof >/dev/null && lsof -i :8000 -i :8501 -i :7474 -i :7687 || true
  echo "[status] Background PIDs:"
  for name in uvicorn streamlit; do
    PID_FILE="$LOG_DIR/$name.pid"
    if [[ -f "$PID_FILE" ]]; then
      echo "  $name: $(cat "$PID_FILE")"
    else
      echo "  $name: not running"
    fi
  done
}

logs() {
  echo "--- uvicorn.log (tail -n 50) ---" && tail -n 50 "$UVICORN_LOG" 2>/dev/null || true
  echo "--- streamlit.log (tail -n 50) ---" && tail -n 50 "$STREAMLIT_LOG" 2>/dev/null || true
}

case "${1:-up}" in
  up)
    ensure_venv
    start_docker
    start_api
    start_ui
    echo "\n[ready] Open UI: http://localhost:8501  | API: http://localhost:8000 | Neo4j: http://localhost:7474"
    ;;
  down)
    stop_bg
    if command -v docker >/dev/null 2>&1; then
      echo "[docker] Compose down"
      docker compose -f "$ROOT_DIR/docker-compose.yml" down
    fi
    echo "[done] Stopped"
    ;;
  status)
    status
    ;;
  logs)
    logs
    ;;
  *)
    echo "Usage: $0 {up|down|status|logs}" >&2
    exit 1
    ;;
 esac
