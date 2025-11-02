# ActCLI-HIC Backlog

## Sprint 0 – Infrastructure & Base Agent
- [x] Package `hw_assessor.py` as an installable module with CLI entrypoint.
- [x] Add unit tests for Markdown generator (fixtures from `hw_assessor-msi-raider-linux.local.md`).
- [ ] Establish packaging/publishing workflow (uv/poetry) and Pin dependencies.
- [ ] Create example inventory (`config/hosts.example.yaml`) with SSH options.

## Sprint 1 – FastAPI Service
- [x] Scaffold FastAPI project layout (`app/main.py`, routers, models).
- [x] Introduce SQLite via SQLModel or SQLAlchemy for hosts/jobs/reports.
- [x] Implement `/hosts` (list/create/update) and `/jobs` (submit assessment request).
- [x] Wire background task queue (FastAPI BackgroundTasks or `asyncio.create_task`).
- [x] Integrate SSH executor using AsyncSSH with timeout/error handling.

## Sprint 2 – Discovery & Caching
- [x] Build Avahi/mDNS discovery probe (async subprocess wrapper for `avahi-browse`).
- [x] Normalize host metadata (hostname, IPv4, vendor) and persist in DB.
- [ ] Schedule periodic refresh and mark stale/offline hosts.

## Sprint 3 – Frontend SPA
- [x] Scaffold React/Vite app under `frontend/` with Tailwind or Chakra.
- [x] Implement host list view with filtering and status tags.
- [x] Build job trigger modal and live status polling.
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

### SPA Export Strategy

- Add comparison view export menu with options: `CSV (client)`, `PDF – in-browser`, `PDF – server download`.
- Build a shared comparison serializer (JS + Python) so both SPA and API produce identical tables.
- Client-side: use `json2csv` for CSV, `@react-pdf/renderer` for PDF; skip heavy tasks on narrow/mobile viewports and link to API export instead.
- API endpoints:
  - `GET /exports/comparison.csv?hosts=...&categories=...`
  - `GET /exports/comparison.pdf?hosts=...&categories=...&theme=ledger|analyst`
  - Return `Attachment` downloads; reuse serializer, guard with auth & rate limits.
- Preserve theme tokens across exports; provide a print-friendly (high-contrast) toggle.
- Document the workflow in the design system so other ActCLI apps follow the same pattern.

### Immediate Next Steps

- [ ] Distribute assessor binary/module automatically to remote hosts (scp or release artifact).
- [ ] Persist assessment history per host and expose comparison over time.
- [ ] Replace comparison placeholders with real metric summaries (CPU/RAM/storage deltas, warnings).
- [ ] Surface Markdown report in the SPA with copy/download controls.
- [ ] Finish CSV/PDF export endpoints and wire client controls.
- [ ] Harden credential management (SSH key selection, sudo policy overrides).
- [ ] Implement optional sudo password prompt for single-machine deployments (in-memory secret, wiped after use).
