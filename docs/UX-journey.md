# Hardware Insight Console – UX Flow (current state)

This document captures how the prototype UI behaves today so we can refine copy, affordances, and onboarding in upcoming sprints.

## 1. Landing (Explore view)
1. **Hosts panel** (left column):
   - Lists registered hosts from `/api/hosts`.
   - If the list is empty, users see an “Import” section that shows raw discovery results (`/api/discover/hosts`).
   - Each discovery item has an _Import_ button that calls `POST /api/discover/hosts/import` and instantly promotes the node into the host list.
2. **Header** (main column):
   - Shows selected host name.
   - “Run assessment” button queues `POST /api/jobs`; status text updates as `GET /api/jobs/{id}` reports `running` → `completed` or `error`.
3. **Upgrade Tips card**:
   - Displays the first Markdown hints from the report payload when an assessment exists.
   - Otherwise shows a reminder to run an assessment.
4. **Category cards** (Memory, Storage, CPU, GPU, Software):
   - Render structured metrics from `/api/hosts/{id}/metrics`.
   - Prior to the first assessment each card displays the “Run an assessment” guidance.

### Empty state → first assessment
- Import a host (or create via `POST /api/hosts`).
- Click “Run assessment” → background job triggers.
- While job is running the button shows “Assessment running…” status.
- After completion the cards refresh in-place; `last seen` timestamp updates.

### Error state
- If SSH/sudo fails the button surfaces the error message returned by `/api/jobs/{id}`.
- User can adjust host metadata (e.g., `ssh_target`, `allow_privileged`) and re-run.

## 2. Compare view
1. **Hosts selector**: multi-select checkboxes driven by `/api/hosts`.
2. **Categories selector**: toggles which comparison columns to show (`overview`, `memory`, `storage`, `cpu`, `gpu`, `software`).
3. **Exports panel**: buttons are placeholders, wired to future CSV/PDF endpoints.
4. **Comparison table**: fetches `/api/comparisons?hosts=…&categories=…` and renders summaries from the latest assessments.
   - For hosts without assessments the table shows “No assessment”.
   - When new jobs complete, the table updates after the next query refetch.

## 3. Discovery flow summary
1. SPA poll `GET /api/discover/hosts` on load.
2. Each undiscovered node displays hostname + first IP/alias.
3. On _Import_, backend creates a host record, copying tags, address, and the first SSH alias as `ssh_target`.
4. Newly imported host appears in the primary list automatically (React Query invalidation).

## 4. Terminology shown to users (current copy)
- **“Run assessment”** – triggers remote hardware probe.
- **“Assessment running …”** – job in progress.
- **“Assessment failed — check backend logs.”** – error state.
- **Tips card** – upgrade suggestions from the payload; first tip is highlighted.
- **Category cards** – values, thresholds, and hints derived from metrics JSON.

## 5. Pain points & improvements to track
- No status chip beside each host (users must click to see when last assessment ran).
- Markdown report content isn’t surfaced yet (only structured metrics).
- Error messages are raw strings from backend; we should provide friendlier guidance.
- Discovery import is hidden once hosts exist; consider a dedicated “Discover” drawer.
- Users cannot edit `allow_privileged` / `ssh_target` from the UI yet (Swagger only).

Use this document as the baseline for UX audits and to script usability sessions.  Update it as flows evolve.
