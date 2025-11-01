# Hardware Insight Console (ActCLI-HIC)

Hardware Insight Console (HIC) turns the existing `hw_assessor.py` hardware profiler into a FastAPI + SPA service that can inventory LAN hosts, run remote assessments over SSH, and present upgrade-friendly reports. This repo currently holds the prototype script, discovery vision, and remote configuration notes while we scaffold the full stack.

The Hardware Insight Console bridges the gap between powerful CLI tooling and approachable reporting for “power casual” users—professionals who rely on their machines but don’t live inside terminals.

## Current Contents
- `agents/hw_assessor/` – Packaged Markdown report generator with module entrypoints.
- `hw_assessor.py` – Backwards-compatible launcher for the packaged assessor.
- `app/` – FastAPI backend scaffold (models, routes, config).
- `hw_assessor-readme.md` – Usage and deployment notes for the script.
- `hw_assessor-msi-raider-linux.local.*` – Sample output/logs captured from a real machine.
- `Vision-Concept.md` – Product strategy, MVP scope, and roadmap.
- `Github -Info.md` – SSH endpoints for GitHub and Gitea remotes.
- `docs/backlog.md` – Development backlog and roadmap.

## Roadmap (MVP Week)
1. Package the hardware assessor for remote execution (Paramiko/AsyncSSH wrapper).
2. FastAPI service skeleton with `/hosts`, `/jobs`, `/reports/<id>` endpoints and SQLite persistence.
3. Background job runner to dispatch assessments and collect Markdown output.
4. React/Vite frontend to trigger runs and render reports.

See `Vision-Concept.md` for full context and long-term plans.

## Git Remotes
- GitHub: `git@github.com:llm-case-studies/ActCLI-HIC.git`
- Gitea: `omv-elbo-gitea:FunGitea/ActCLI-HIC.git`

Use `git remote -v` after cloning to confirm both are configured.

## Getting Started
```bash
# create a virtual environment for upcoming FastAPI work
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
```

Once the FastAPI service lands, we will add `requirements.txt`, backend entrypoints, and frontend tooling. For now, review the vision doc and script to align on architecture.

## Using the Hardware Assessor Locally
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -e .  # installs the packaged assessor (hw-assessor entrypoint)

# run the assessor via module or script
hw-assessor | tee "hw_assessor-$(hostname).md"
# or
python -m agents.hw_assessor
```

The legacy `./hw_assessor.py` launcher remains available for compatibility and delegates to the packaged module.

## Testing
Unit tests cover pure helper logic (parsing, recommendations) and serve as a foundation for broader mocks.
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -e .
pip install pytest
pytest
```

The repository’s `pyproject.toml` defines project metadata, entry points, and will grow with API dependencies as the FastAPI service takes shape.

## Running the API Skeleton
```bash
uvicorn app.main:app --reload
```

The scaffold exposes REST endpoints under `/api`:
- `GET /api/hosts` — list registered hosts.
- `POST /api/hosts` — create a host record.
- `POST /api/jobs` — queue an assessment (currently a placeholder job that returns canned output).
- `GET /api/jobs`, `GET /api/jobs/{id}`, `GET /api/reports/{job_id}` — inspect queued/completed work.

SQLite data is stored under `data/hic.db` by default; override with `HIC_DATABASE_URL` if needed.
