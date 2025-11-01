# Hardware Insight Console (ActCLI-HIC)

Hardware Insight Console (HIC) turns the existing `hw_assessor.py` hardware profiler into a FastAPI + SPA service that can inventory LAN hosts, run remote assessments over SSH, and present upgrade-friendly reports. This repo currently holds the prototype script, discovery vision, and remote configuration notes while we scaffold the full stack.

## Current Contents
- `hw_assessor.py` – Markdown report generator for the local host.
- `hw_assessor-readme.md` – Usage and deployment notes for the script.
- `hw_assessor-msi-raider-linux.local.*` – Sample output/logs captured from a real machine.
- `Vision-Concept.md` – Product strategy, MVP scope, and roadmap.
- `Github -Info.md` – SSH endpoints for GitHub and Gitea remotes.

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
