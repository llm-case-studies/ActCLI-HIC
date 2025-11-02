#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_PATH="${ROOT_DIR}/.venv"
API_PORT="${HIC_API_PORT:-9100}"
VITE_PORT="${HIC_VITE_PORT:-5173}"

if [[ ! -d "${VENV_PATH}" ]]; then
  echo "Virtual environment not found at ${VENV_PATH}." >&2
  echo "Create it with: python3 -m venv .venv" >&2
  exit 1
fi

source "${VENV_PATH}/bin/activate"

if [[ -n "${HIC_REQUIREMENTS:-}" ]]; then
  pip install -r "${ROOT_DIR}/${HIC_REQUIREMENTS}"
fi

function start_api() {
  echo "Starting FastAPI (port ${API_PORT})..."
  uvicorn app.main:app --host 0.0.0.0 --port "${API_PORT}" --reload
}

function start_frontend() {
  export VITE_API_BASE="http://localhost:${API_PORT}/api"
  cd "${ROOT_DIR}/frontend"
  if [[ ! -d node_modules ]]; then
    echo "Installing frontend dependencies..."
    npm install
  fi
  echo "Starting Vite dev server (port ${VITE_PORT}) with API base ${VITE_API_BASE}"
  npm run dev -- --host 0.0.0.0 --port "${VITE_PORT}"
}

case "${1:-}" in
  api)
    start_api
    ;;
  frontend)
    start_frontend
    ;;
  all|dev)
    export VITE_API_BASE="http://localhost:${API_PORT}/api"
    cd "${ROOT_DIR}/frontend"
    if [[ ! -d node_modules ]]; then
      echo "Installing frontend dependencies..."
      npm install
    fi
    echo "Launching FastAPI and Vite (ports ${API_PORT} / ${VITE_PORT})"
    npm run dev -- --host 0.0.0.0 --port "${VITE_PORT}" -- --api-port "${API_PORT}"
    ;;
  *)
    cat <<USAGE
Usage: ./hic-dev.sh [api|frontend|dev]
  api       Start FastAPI backend (default port 9100)
  frontend  Start Vite dev server (proxies to API port)
  dev       (reserved for future combined workflow)

Environment variables:
  HIC_API_PORT   Backend port (default 9100)
  HIC_VITE_PORT  Frontend port (default 5173)
  VITE_API_BASE  Overrides API base URL for the SPA
  HIC_REQUIREMENTS Optional requirements file to install before launching
USAGE
    ;;
 esac
