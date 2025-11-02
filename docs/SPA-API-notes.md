# SPA ↔ API Wiring Notes

## Current endpoints consumed by the frontend
- `GET /api/hosts` — returns registered hosts.
- `GET /api/comparisons?hosts=` — returns placeholder comparison metrics.
- `GET /api/discover/hosts` — used for discovery view.
- `POST /api/discover/hosts/import` — promote discovered hostnames into the main host table.

## Dev workflow
- `./hic-dev.sh api` — starts FastAPI on port 9100; uses `.venv`.
- `./hic-dev.sh frontend` — starts Vite dev server, sets `VITE_API_BASE=http://localhost:9100/api` automatically.
- Override API port via `HIC_API_PORT`; the frontend script respects that and forwards it to `VITE_API_BASE`.

## Known limitations
- `/api/comparisons` currently returns stub metrics; replace with real assessment data once jobs are wired up.
- Discovery results are not persisted automatically; user must create hosts explicitly.
