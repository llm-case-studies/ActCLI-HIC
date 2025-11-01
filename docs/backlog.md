# ActCLI-HIC Backlog

## Sprint 0 – Infrastructure & Base Agent
- [ ] Package `hw_assessor.py` as an installable module with CLI entrypoint.
- [ ] Add unit tests for Markdown generator (fixtures from `hw_assessor-msi-raider-linux.local.md`).
- [ ] Establish packaging/publishing workflow (uv/poetry) and Pin dependencies.
- [ ] Create example inventory (`config/hosts.example.yaml`) with SSH options.

## Sprint 1 – FastAPI Service
- [ ] Scaffold FastAPI project layout (`app/main.py`, routers, models).
- [ ] Introduce SQLite via SQLModel or SQLAlchemy for hosts/jobs/reports.
- [ ] Implement `/hosts` (list/create/update) and `/jobs` (submit assessment request).
- [ ] Wire background task queue (FastAPI BackgroundTasks or `asyncio.create_task`).
- [ ] Integrate SSH executor using AsyncSSH with timeout/error handling.

## Sprint 2 – Discovery & Caching
- [ ] Build Avahi/mDNS discovery probe (async subprocess wrapper for `avahi-browse`).
- [ ] Normalize host metadata (hostname, IPv4, vendor) and persist in DB.
- [ ] Schedule periodic refresh and mark stale/offline hosts.

## Sprint 3 – Frontend SPA
- [ ] Scaffold React/Vite app under `frontend/` with Tailwind or Chakra.
- [ ] Implement host list view with filtering and status tags.
- [ ] Build job trigger modal and live status polling.
- [ ] Render Markdown report with `react-markdown` + copy/download actions.

## Sprint 4 – Knowledge Layer & UX Polish
- [ ] Externalize upgrade hints (`data/platforms/*.yaml`).
- [ ] Present upgrade opportunities with sourcing links.
- [ ] Introduce report history diffing (per host timeline).
- [ ] Add authentication (bearer token via env/config) for API and SPA.

## Tooling & Ops
- [ ] Configure pre-commit hooks (ruff, black, mypy, eslint, prettier).
- [ ] Add CI workflows (GitHub Actions/Gitea Actions parity) for lint/test/build.
- [ ] Provide Docker Compose for dev stack (API, frontend, optional postgres).
- [ ] Document deployment steps (systemd service, reverse proxy, HTTPS).
