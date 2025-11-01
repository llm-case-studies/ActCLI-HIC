  # Hardware Insight Console – Vision & Concept

  ## 1. Executive Summary
  The Hardware Insight Console (HIC) bridges the gap between command-line hardware tools and approachable reporting for “power casual” users—professionals who rely on their machines but don’t live inside terminals. By pairing automated host discovery
  with on-demand profiling, HIC delivers Markdown/HTML reports that surface upgrade headroom, workload suitability, and vendor references in a single click.

  Target personas: actuarial analysts, content creators, indie developers, tech-savvy managers—teams that need accurate hardware intel without learning `dmidecode`.

  ## 2. Problem Statement
  1. CLI tools are powerful but scattered; interpreting their output requires expertise.
  2. Existing GUIs (e.g., Cockpit) lack deep slot/part-number context and historical tracking.
  3. Multi-machine environments demand repeatable inventory, yet rolling your own scripts per box is tedious.

  ## 3. Solution Overview
  - **Discovery Layer**: Leverage Avahi/MDNS for zero-config host discovery. Cache host metadata and support manual enrollment for remote networks.
  - **Execution Layer**: Use SSH (Paramiko/AsyncSSH) to ship and run the upgraded `hw_assessor.py`, collecting Markdown + optional JSON.
  - **Presentation Layer (SPA)**: FastAPI-backed API serving a React/Vue SPA. Users browse hosts, trigger assessments, and view rendered reports with upgrade suggestions and links to vendor docs.
  - **Knowledge Layer**: Configurable mappings (per model, RAM/SSD part numbers) providing curated upgrade paths (e.g., top-rated DDR5 SODIMMs) and official service manuals.

  ## 4. MVP Scope (≤1 week)
  - Service:
    - FastAPI app with endpoints: `/hosts`, `/jobs`, `/reports/<id>`.
    - Background job runner (celery/rq or FastAPI’s background tasks) for SSH execution.
    - Simple SQLite persistence for host cache and job metadata.
  - SPA:
    - Host list with tags (online/offline, last scan).
    - “Run Assessment” button; results rendered with `marked`/`react-markdown`.
    - Download button for raw Markdown.
  - Script integration:
    - Package the enhanced `hw_assessor.py`; auto-upload if missing or outdated on target host.
    - Sudo prompt handling via `sudo -S` or documented requirement for passwordless execution of the script.
  - Security:
    - SSH key management (per-host key path, optional vault for passphrases).
    - API authentication token (bearer) for SPA.

  ## 5. Roadmap Highlights
  - **Phase 2**: Persistent history, diffing, alerting (e.g., RAM removed, SMART warnings).
  - **Phase 3**: Pluggable tests (memtester, stress-ng), scheduled runs, email/Slack summaries.
  - **Phase 4**: Vendor catalogue integration; auto-suggest purchase links with part validation.
  - **Phase 5**: Optional agent to push results when machines are intermittently reachable.

  ## 6. Alignment with AtcCLI
  AtcCLI positions itself as tooling for actuaries and analytically minded professionals. HIC complements that mission by demystifying hardware sizing for compute-heavy workloads—Monte Carlo sims, ML inference, media rendering. Bundling under the AtcCLI
  umbrella adds ecosystem value: same CLI/SPA style, shared authentication and reporting conventions.

  ## 7. Competitive Landscape
  - Cockpit/Netdata: great for per-host monitoring, weak on upgrade intelligence.
  - RMM platforms: heavy, commercial, overkill for small teams.
  - Custom scripts: fragile and siloed, no central UI.

  HIC sits between raw CLI and enterprise RMM—lightweight, open, approachable.

  ## 8. Success Metrics
  - Time-to-assessment (<30 seconds from click to report for LAN hosts).
  - Coverage (number of hosts inventoried weekly).
  - Conversion rate from “unassessed” to “baseline recorded”.
  - User feedback: clarity of upgrade recommendations, trust in vendor links.

  ## 9. Risks & Mitigations
  - **SSH permissions**: document how to permit passwordless execution or capture passwords securely; fail gracefully with actionable errors.
  - **Avahi scope**: optional manual host entry for remote/DC nodes.
  - **User trust**: open-source code, clear logging, no silent background actions.

  ## 10. Next Steps
  1. Stand up repo (`AtcCLI/hardware-insight-console`), seed with script/README/vision doc.
  2. Scaffold FastAPI + SPA skeleton; integrate current Markdown generator.
  3. Implement Avahi probe & discovery cache.
  4. Add integration tests (mock SSH) and sample data.
  5. Prepare launch blog/tutorial for the target audience.

  - Repo README draft (after you create the project)

  # Hardware Insight Console

  FastAPI + SPA tool that discovers hosts via Avahi, runs the `hw_assessor.py`
  hardware profiler over SSH, and renders upgrade-friendly Markdown reports.

  ## Features
  - Zero-config discovery of LAN nodes (Avahi/MDNS) plus manual enrollment.
  - One-click hardware assessment with Markdown/HTML output.
  - Upgrade hints: RAM ceiling, storage slots, vendor links.
  - API-first: integrate with notebooks, automation, or AtcCLI scripts.

  ## Getting Started
  1. Clone and install
     ```bash
     git clone https://github.com/AtcCLI/hardware-insight-console.git
     cd hardware-insight-console
     uv venv && source .venv/bin/activate      # or poetry/pipenv
     pip install -r requirements.txt

  2. Configure SSH credentials in config/hosts.yaml or environment variables.
  3. Run development stack

     uvicorn app.main:app --reload
     npm install --prefix frontend
     npm run dev --prefix frontend
  4. Open http://localhost:3000 to browse hosts and request assessments.

  ## Project Structure

  - app/ – FastAPI services (discovery, job queue, report storage)
  - frontend/ – SPA (React/Vite or Vue)
  - agents/hw_assessor.py – Hardware profiler shipped to nodes
  - docs/ – Vision, architecture, roadmap

  ## Requirements

  - Python 3.11+
  - Node 18+ (for the SPA)
  - Avahi utilities (avahi-browse) on the controller host
  - Target hosts must have Python 3, sudo access, and standard CLI tools (dmidecode, lsblk, lscpu, lspci, free); optional extras (nvme, nvidia-smi) enrich the report.

  ## Roadmap

  - Persist report history with diff view
  - Pluggable stress-test modules
  - Alerting for hardware regressions
  - Vendor catalogue integration

  ## License

  MIT (or choose one)


  - Timeline & AtcCLI fit
    - Under the AtcCLI umbrella makes sense: same target audience (actuaries and analytical professionals) who need hardware sizing clarity; gives AtcCLI another flagship tool.
    - MVP within a week is realistic: the script and README already exist; allocate time for FastAPI scaffold, Avahi integration, SSH job execution, and SPA skeleton (~3–5 focused days plus polish).
    - Suggest forming a small backlog (discovery → job runner → UI → polish) and tracking via GitHub Projects.

