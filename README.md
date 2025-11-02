# Hardware Insight Console (ActCLI-HIC)

Hardware Insight Console (HIC) bridges the gap between low-level CLI hardware probes and approachable reports. It discovers hosts on the LAN, runs the packaged `agents.hw_assessor` remotely (or locally), captures Markdown + structured metrics, and presents them through a React SPA backed by FastAPI.

## Highlights
- **Remote assessments** – FastAPI queues jobs that SSH into hosts (or runs locally) and executes `hw_assessor` with JSON output. Markdown plus structured metrics/ratings/tips are persisted per host.
- **Autodiscovery** – Avahi + SSH config inspection populate `/api/discover/hosts`; a single click promotes discoveries into the host table.
- **Theme-aware SPA** – React/Vite UI ships “Explore” and “Compare” modes, live theme switching, upgrade hints, and job triggers.
- **Job/status tracking** – `/api/jobs` exposes progress/errors so the UI can poll and render actionable feedback.
- **One-command dev loop** – `hic-dev.sh` starts FastAPI (port 9100) and Vite (port 5173) with consistent environment variables.

## Repository structure
```
agents/                 # Packaged assessor (`python -m agents.hw_assessor --output json`)
app/                    # FastAPI service (models, routes, discovery helpers)
frontend/               # React/Vite SPA
docs/                   # Backlog, theme reference, SPA ↔ API notes, etc.
hic-dev.sh              # Helper script for dev workflow
```

See `Vision-Concept.md` for the long-term product vision and `docs/backlog.md` for sprint-level tasks.

## Quick start
```bash
# clone and enter repo
cd ActCLI-HIC

# Python env
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -e .
pip install "fastapi[standard]" uvicorn sqlmodel pydantic-settings typer

# Frontend deps (Node 18+)
cd frontend
npm install
```

### Dev workflow
```bash
# terminal 1 – API on http://localhost:9100
./hic-dev.sh api

# terminal 2 – SPA on http://localhost:5173 (proxies to API)
./hic-dev.sh frontend
```
The script respects `HIC_API_PORT` / `HIC_VITE_PORT` overrides and sets `VITE_API_BASE` automatically.

### Manual startup
```bash
uvicorn app.main:app --host 0.0.0.0 --port 9100 --reload
cd frontend && npm run dev
```

## Onboarding hosts
1. **Discover** – Open the SPA (Explore view) or call `GET /api/discover/hosts`. Avahi + SSH config entries appear with import buttons.
2. **Import** – Click “Import” or `POST /api/discover/hosts/import` with hostnames to promote them into `/api/hosts`.
3. **Configure SSH** – Ensure each host has an `ssh_target` you can reach non-interactively (e.g. `funhome@omv-elbo.local`). Update `allow_privileged` if passwordless sudo is unavailable.
4. **Install assessor** – On each remote machine: `pip install actcli-hw-assessor` so both `python3 -m agents.hw_assessor` and `hw-assessor` work.
5. **Decide on sudo strategy** – Options range from passwordless sudo (see `docs/sudo-access.md`) to per-run prompting for single-machine setups.
6. **Run assessment** – Use the “Run assessment” button or `POST /api/jobs`. Successful jobs populate `/api/hosts/{id}/metrics` and refresh the comparison grid.

## Key API endpoints
- `GET /api/hosts` – Registered hosts (includes `ssh_target`, privilege flags, timestamps).
- `POST /api/hosts` / `PATCH /api/hosts/{id}` – Manage host metadata.
- `GET /api/discover/hosts` → `POST /api/discover/hosts/import` – Discovery workflow.
- `POST /api/jobs` → `GET /api/jobs/{id}` – Queue and monitor assessments.
- `GET /api/hosts/{id}/metrics` – Latest Markdown + structured metrics bundle for a host.
- `GET /api/comparisons?hosts=…&categories=…` – Aggregated data feeding the compare grid.

Swagger UI lives at `http://localhost:9100/docs`.

## Testing
```bash
source .venv/bin/activate
pytest
```
(18 unit tests cover discovery utilities, assessor helpers, and subprocess guardrails.)

## Additional docs
- `docs/actcli-theme-reference.md` – Shared color palettes for ActCLI projects.
- `docs/SPA-API-notes.md` – Frontend ↔ backend contract notes.
- `docs/UX-journey.md` – Current UI flow (onboarding, assessments, compare view).
- `docs/sudo-access.md` – Guidelines for configuring passwordless sudo and dedicated accounts.
- `docs/backlog.md` – Sprint backlog & next steps.

## Next steps (high-level)
- Package/ship the assessor automatically to remote hosts (scp or artifact download).
- Persist assessment history & expose comparisons over time.
- Wire CSV/PDF exports to real data (client + server endpoints).
- Harden credential management (SSH key selection, sudo policy). EOF
