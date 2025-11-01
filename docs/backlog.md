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
- [ ] Build modular insights panel so users can toggle deep-dive modules.

## Sprint 5 – Operational Insights Expansion
- [ ] Collect OS/package inventory (e.g., `rpm`, `dpkg`, `flatpak`) with configurable depth.
- [ ] Report local accounts, sudoers membership, and recent logins with privacy-safe filtering.
- [ ] Capture filesystem utilization (`df`, quotas) and alert thresholds.
- [ ] Enumerate running services/containers (systemd, Docker, Podman) with resource stats.
- [ ] Surface software/version diffs between assessments to highlight drift.

## Sprint 6 – Intelligence & Knowledge Services
- [ ] Add optional web lookup pipeline (cached HTTP client + rate limiting) for vendor docs and CVEs.
- [ ] Integrate lightweight (~3B) local LLM via REST/gRPC for on-device summarization and Q&A.
- [ ] Provide prompt templates for “explain this report”, “suggest next upgrades”, “compare hosts”.
- [ ] Expose AI-driven insights through API and SPA (chat sidebar, contextual tooltips).
- [ ] Implement opt-in data governance controls (no external calls, anonymized logs, prompt history purge).

## Tooling & Ops
- [ ] Configure pre-commit hooks (ruff, black, mypy, eslint, prettier).
- [ ] Add CI workflows (GitHub Actions/Gitea Actions parity) for lint/test/build.
- [ ] Provide Docker Compose for dev stack (API, frontend, optional postgres).
- [ ] Document deployment steps (systemd service, reverse proxy, HTTPS).
