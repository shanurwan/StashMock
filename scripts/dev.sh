#!/usr/bin/env bash
set -euo pipefail

# Usage:
#   ./scripts/dev.sh start [sync|offload]
#   ./scripts/dev.sh restart_portfolio [sync|offload]
#   ./scripts/dev.sh stop
#   ./scripts/dev.sh status

MODE="${2:-offload}"   # default: offload
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
LOG_DIR="$ROOT_DIR/.logs"
RUN_DIR="$ROOT_DIR/.run"
PY="$ROOT_DIR/.venv/bin/python"
UV="$ROOT_DIR/.venv/bin/uvicorn"

mkdir -p "$LOG_DIR" "$RUN_DIR"

ensure_python() {
  if [[ ! -x "$PY" ]]; then
    python -m venv "$ROOT_DIR/.venv"
    "$ROOT_DIR/.venv/bin/pip" install --upgrade pip >/dev/null
    "$ROOT_DIR/.venv/bin/pip" install "fastapi>=0.112" "uvicorn[standard]>=0.30" "redis>=5" "pydantic>=2" prometheus-fastapi-instrumentator >/dev/null
  fi
}

ensure_redis() {
  if ! command -v redis-server >/dev/null 2>&1; then
    if command -v apt-get >/dev/null 2>&1; then
      sudo apt-get update -y && sudo apt-get install -y redis-server
    else
      echo "redis-server not found and no apt-get. Please install Redis manually." >&2
      exit 1
    fi
  fi
  # Start if not running
  if ! redis-cli ping >/dev/null 2>&1; then
    redis-server --daemonize yes
    sleep 1
  fi
}

start_service() {
  local name="$1" port="$2" module="$3"
  local extra_env="${4:-}"
  if pgrep -f "$module" >/dev/null 2>&1; then
    echo "[$name] already running on :$port"
    return 0
  fi
  echo "Starting $name on :$port"
  # shellcheck disable=SC2086
  nohup env $extra_env "$UV" "$module" --port "$port" >"$LOG_DIR/$name.log" 2>&1 &
  echo $! > "$RUN_DIR/$name.pid"
  sleep 1
}

stop_service() {
  local name="$1" module="$2"
  if [[ -f "$RUN_DIR/$name.pid" ]]; then
    kill "$(cat "$RUN_DIR/$name.pid")" || true
    rm -f "$RUN_DIR/$name.pid"
  fi
  pkill -f "$module" || true
}

case "${1:-}" in
  start)
    ensure_python
    ensure_redis
    # notifications & worker first
    start_service "notification_service" 8002 "api.notification_service.main:app"
    start_service "worker_service" 8003 "api.worker_service.main:app"
    # portfolio with mode
    if [[ "$MODE" == "sync" ]]; then
      start_service "portfolio_service" 8001 "api.portfolio_service.main:app" "SYNC_NOTIFICATIONS=1"
    else
      start_service "portfolio_service" 8001 "api.portfolio_service.main:app" "SYNC_NOTIFICATIONS=0"
    fi
    echo "All services started. Logs => $LOG_DIR"
    ;;
  restart_portfolio)
    ensure_python
    # stop only portfolio and start with new mode
    stop_service "portfolio_service" "api.portfolio_service.main:app"
    if [[ "$MODE" == "sync" ]]; then
      start_service "portfolio_service" 8001 "api.portfolio_service.main:app" "SYNC_NOTIFICATIONS=1"
    else
      start_service "portfolio_service" 8001 "api.portfolio_service.main:app" "SYNC_NOTIFICATIONS=0"
    fi
    ;;
  stop)
    stop_service "portfolio_service" "api.portfolio_service.main:app"
    stop_service "notification_service" "api.notification_service.main:app"
    stop_service "worker_service" "api.worker_service.main:app"
    # Try to stop redis if we started it
    redis-cli shutdown >/dev/null 2>&1 || true
    echo "Stopped."
    ;;
  status)
    echo "Ports:"
    (ss -lnt 2>/dev/null || netstat -lnt 2>/dev/null) | grep -E '(:8001|:8002|:8003)' || true
    echo "Processes:"
    pgrep -fal "uvicorn .*api\." || true
    ;;
  *)
    echo "Usage: $0 {start|restart_portfolio|stop|status} [sync|offload]"
    exit 1
    ;;
esac
