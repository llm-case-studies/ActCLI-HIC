#!/usr/bin/env bash

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DEFAULT_VENV_PY="${REPO_ROOT}/.venv/bin/python"

if [[ -n "${PYTHON_BIN:-}" ]]; then
  PYTHON_CMD="${PYTHON_BIN}"
elif [[ -x "${DEFAULT_VENV_PY}" ]]; then
  PYTHON_CMD="${DEFAULT_VENV_PY}"
else
  PYTHON_CMD="python3"
fi

# Reserve 9100-9199 for ActCLI services unless overridden.
PORT="${HIC_PORT:-9100}"
UVICORN_MODULE="app.main:app"

usage() {
  cat <<'EOF'
Hardware Insight Console helper

USAGE
  ./hic.sh app start        Start API service on ${HIC_PORT:-9100}
  ./hic.sh app stop         Terminate any process bound to the service port
  ./hic.sh app restart      Stop then start the API service
  ./hic.sh test unit        Run unit tests (default: ./tests)
  ./hic.sh test api         Run API tests    (./tests/api if present)
  ./hic.sh test e2e         Run E2E tests    (./tests/e2e if present)
  ./hic.sh test all         Run unit, API, and E2E test suites in order

ENVIRONMENT
  HIC_PORT       Override the default service port (default: 9100)
  PYTHON_BIN     Explicit python executable to use
  HIC_RELOAD=1   Start uvicorn with --reload

EOF
}

ensure_pytest() {
  if ! "${PYTHON_CMD}" -m pytest --version >/dev/null 2>&1; then
    echo "ERROR: pytest is not available for ${PYTHON_CMD}. Install project optional deps (pip install -e .[test])" >&2
    exit 1
  fi
}

kill_port() {
  local port="$1"
  local pids=""

  if command -v lsof >/dev/null 2>&1; then
    pids="$(lsof -t -i tcp:"${port}" 2>/dev/null || true)"
  elif command -v fuser >/dev/null 2>&1; then
    pids="$(fuser "${port}/tcp" 2>/dev/null | tr ' ' '\n' || true)"
  fi

  if [[ -z "${pids}" ]]; then
    return
  fi

  echo "Stopping processes on port ${port}: ${pids}" >&2
  while read -r pid; do
    [[ -z "${pid}" ]] && continue
    if kill "${pid}" 2>/dev/null; then
      wait "${pid}" 2>/dev/null || true
    fi
  done <<<"${pids}"
}

start_app() {
  kill_port "${PORT}"

  local uvicorn_args=("${UVICORN_MODULE}" "--host" "0.0.0.0" "--port" "${PORT}")
  if [[ "${HIC_RELOAD:-0}" != "0" ]]; then
    uvicorn_args+=("--reload")
  fi

  echo "Starting API on port ${PORT} using ${PYTHON_CMD}" >&2
  exec "${PYTHON_CMD}" -m uvicorn "${uvicorn_args[@]}"
}

run_tests() {
  local target="$1"
  shift || true

  ensure_pytest

  case "${target}" in
    unit)
      echo "Running unit tests" >&2
      "${PYTHON_CMD}" -m pytest "${REPO_ROOT}/tests" "$@"
      ;;
    api)
      if [[ -d "${REPO_ROOT}/tests/api" ]]; then
        echo "Running API tests" >&2
        "${PYTHON_CMD}" -m pytest "${REPO_ROOT}/tests/api" "$@"
      else
        echo "INFO: No API tests directory found (tests/api). Skipping." >&2
      fi
      ;;
    e2e)
      if [[ -d "${REPO_ROOT}/tests/e2e" ]]; then
        echo "Running E2E tests" >&2
        "${PYTHON_CMD}" -m pytest "${REPO_ROOT}/tests/e2e" "$@"
      else
        echo "INFO: No E2E tests directory found (tests/e2e). Skipping." >&2
      fi
      ;;
    all)
      run_tests unit "$@"
      run_tests api "$@"
      run_tests e2e "$@"
      ;;
    *)
      echo "ERROR: Unknown test target '${target}'" >&2
      usage
      exit 1
      ;;
  esac
}

case "${1:-}" in
  app)
    action="${2:-}"; shift 2 || true
    case "${action}" in
      start)
        start_app "$@"
        ;;
      stop)
        kill_port "${PORT}"
        ;;
      restart)
        kill_port "${PORT}"
        start_app "$@"
        ;;
      *)
        echo "ERROR: Unknown app action '${action}'" >&2
        usage
        exit 1
        ;;
    esac
    ;;
  test)
    run_tests "${2:-unit}" "${@:3}"
    ;;
  *)
    usage
    ;;
esac
