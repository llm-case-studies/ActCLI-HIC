"""API routes for the Hardware Insight Console."""

from __future__ import annotations

import json
import socket
import subprocess
from datetime import datetime
from typing import Any, Iterable

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, status
from sqlmodel import Session, select

from .. import models, discovery
from ..db import get_session, init_db, session_scope
from ..schemas import (
    ComparisonMetric,
    DiscoveryImportRequest,
    HostCreate,
    HostRead,
    HostUpdate,
    HostDiscovery,
    HostCheckRequest,
    HostCheckResponse,
    HostMetrics,
    JobCreate,
    JobRead,
    ReportRead,
)
from agents import hw_assessor

router = APIRouter()

LOCAL_ADDRESS_TOKENS = {"localhost", "127.0.0.1", "::1"}
LOCAL_HOSTNAMES = {socket.gethostname().lower(), socket.getfqdn().lower()}
SSH_BASE_ARGS = [
    "ssh",
    "-o",
    "BatchMode=yes",
    "-o",
    "StrictHostKeyChecking=no",
    "-o",
    "ConnectTimeout=30",
]
ASSESSMENT_TIMEOUT = 900

COMPARISON_CATEGORIES = {
    "overview": "Overview",
    "memory": "Memory",
    "storage": "Storage",
    "cpu": "CPU",
    "gpu": "GPU",
    "software": "Software",
}


def _parse_tags(tags: str | None) -> list[str]:
    if not tags:
        return []
    return [tag.strip() for tag in tags.split(",") if tag.strip()]


def _tags_to_string(tags: Iterable[str] | None) -> str | None:
    if not tags:
        return None
    cleaned = [tag.strip() for tag in tags if tag.strip()]
    return ",".join(cleaned) if cleaned else None


def _host_to_schema(host: models.Host) -> HostRead:
    return HostRead(
        id=host.id,
        hostname=host.hostname,
        address=host.address,
        tags=_parse_tags(host.tags),
        source=host.source,
        notes=host.notes,
        is_active=host.is_active,
        allow_privileged=host.allow_privileged,
        ssh_target=host.ssh_target,
        last_seen_at=host.last_seen_at,
        created_at=host.created_at,
    )


def _job_to_schema(job: models.AssessmentJob) -> JobRead:
    return JobRead(
        id=job.id,
        host_id=job.host_id,
        status=job.status,
        requested_at=job.requested_at,
        started_at=job.started_at,
        finished_at=job.finished_at,
        error_message=job.error_message,
    )


def _report_to_schema(report: models.Report) -> ReportRead:
    return ReportRead(
        id=report.id,
        job_id=report.job_id,
        rendered_markdown=report.rendered_markdown,
        raw_payload=report.raw_payload,
        created_at=report.created_at,
    )


def _normalize_token(value: str | None) -> str | None:
    if not value:
        return None
    return value.strip()


def _is_local_host(host: models.Host) -> bool:
    for value in (
        _normalize_token(host.ssh_target),
        _normalize_token(host.address),
        _normalize_token(host.hostname),
    ):
        if not value:
            continue
        lower = value.lower()
        if lower in LOCAL_ADDRESS_TOKENS or lower in LOCAL_HOSTNAMES:
            return True
    return False


def _parse_json_output(text: str) -> dict[str, Any]:
    candidate = text.strip()
    if not candidate:
        raise RuntimeError("Remote assessor returned empty output")
    try:
        return json.loads(candidate)
    except json.JSONDecodeError:
        idx = candidate.find("{")
        if idx != -1:
            trimmed = candidate[idx:]
            try:
                return json.loads(trimmed)
            except json.JSONDecodeError as exc:
                raise RuntimeError(f"Failed to parse JSON output: {candidate}") from exc
        raise


def _run_remote_assessment(host: models.Host) -> dict[str, Any]:
    target = _normalize_token(host.ssh_target) or _normalize_token(host.address) or host.hostname
    if not target:
        raise RuntimeError("Host is missing address or SSH target")

    primary_command = "python3 -m agents.hw_assessor --output json"
    fallback_command = "hw-assessor --output json"
    if host.allow_privileged:
        primary_command = f"sudo -n {primary_command} || {primary_command}"
        fallback_command = f"sudo -n {fallback_command} || {fallback_command}"

    remote_command = f"{primary_command} || {fallback_command}"

    proc = subprocess.run(
        SSH_BASE_ARGS + [target, remote_command],
        capture_output=True,
        text=True,
        timeout=ASSESSMENT_TIMEOUT,
    )

    if proc.returncode != 0:
        stderr = proc.stderr.strip() or proc.stdout.strip() or "SSH command failed"
        raise RuntimeError(stderr)

    return _parse_json_output(proc.stdout)


def _run_local_assessment() -> dict[str, Any]:
    try:
        hw_assessor.configure_privileges(mode="auto", prompt_password=False)
    except SystemExit as exc:
        raise RuntimeError("Local assessor requires sudo; configure passwordless sudo or run as root.") from exc
    return hw_assessor.generate_report_data()


def _collect_assessment_for_host(host: models.Host) -> dict[str, Any]:
    return _run_local_assessment() if _is_local_host(host) else _run_remote_assessment(host)


def _latest_report_with_payload(session: Session, host_id: int) -> tuple[models.Report | None, dict[str, Any] | None]:
    stmt = (
        select(models.Report)
        .join(models.AssessmentJob, models.Report.job_id == models.AssessmentJob.id)
        .where(models.AssessmentJob.host_id == host_id)
        .order_by(models.Report.created_at.desc())
    )
    report = session.exec(stmt).first()
    if not report or not report.raw_payload:
        return report, None
    try:
        payload = json.loads(report.raw_payload)
    except json.JSONDecodeError:
        payload = None
    return report, payload


@router.on_event("startup")
def startup_event() -> None:
    init_db()


@router.get("/hosts", response_model=list[HostRead])
def list_hosts(session: Session = Depends(get_session)) -> list[HostRead]:
    hosts = session.exec(select(models.Host)).all()
    return [_host_to_schema(host) for host in hosts]


@router.get("/hosts/{host_id}/metrics", response_model=HostMetrics)
def get_host_metrics(host_id: int, session: Session = Depends(get_session)) -> HostMetrics:
    host = session.get(models.Host, host_id)
    if not host:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Host not found")

    report, payload = _latest_report_with_payload(session, host_id)
    if not report or not payload:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No assessment available for this host")

    return HostMetrics(
        host_id=host_id,
        collected_at=report.created_at,
        markdown=payload.get("markdown", ""),
        metrics=payload.get("metrics", {}),
        ratings=payload.get("ratings", {}),
        tips=payload.get("tips", []),
        storage_hint=payload.get("storage_hint"),
        system=payload.get("system", {}),
    )


@router.get("/discover/hosts", response_model=list[HostDiscovery])
def discover_hosts(session: Session = Depends(get_session)) -> list[HostDiscovery]:
    discovered = discovery.discover_hosts()
    known_hosts = session.exec(select(models.Host)).all()
    lookup = {discovery.normalize_hostname(host.hostname): host for host in known_hosts}

    results: list[HostDiscovery] = []
    for entry in discovered:
        host = lookup.get(discovery.normalize_hostname(entry.hostname))
        results.append(
            HostDiscovery(
                hostname=entry.hostname,
                addresses=entry.addresses,
                sources=entry.sources,
                tags=entry.tags,
                ssh_aliases=entry.ssh_aliases,
                known_host_id=host.id if host else None,
                is_active=host.is_active if host else None,
                allow_privileged=host.allow_privileged if host else None,
                warnings=entry.warnings,
            )
        )
    results.sort(key=lambda item: item.hostname)
    return results


@router.post("/discover/hosts/check", response_model=HostCheckResponse)
def check_host(payload: HostCheckRequest) -> HostCheckResponse:
    result = discovery.verify_ssh(payload.target, timeout=payload.timeout or 5)
    return HostCheckResponse(
        target=result.target,
        reachable=result.reachable,
        authenticated=result.authenticated,
        returncode=result.returncode,
        stdout=result.stdout,
        stderr=result.stderr,
    )


@router.post("/discover/hosts/import", response_model=list[HostRead])
def import_discovered(
    payload: DiscoveryImportRequest,
    session: Session = Depends(get_session),
) -> list[HostRead]:
    if not payload.hostnames:
        return []

    existing = {
        discovery.normalize_hostname(host.hostname): host
        for host in session.exec(select(models.Host)).all()
    }

    discovered = {
        discovery.normalize_hostname(entry.hostname): entry
        for entry in discovery.discover_hosts()
    }

    imported: list[HostRead] = []
    for raw_name in payload.hostnames:
        key = discovery.normalize_hostname(raw_name)
        if key in existing:
            imported.append(_host_to_schema(existing[key]))
            continue
        entry = discovered.get(key)
        if not entry:
            continue

        tags = _tags_to_string(entry.tags)
        host = models.Host(
            hostname=entry.hostname,
            address=entry.addresses[0] if entry.addresses else None,
            tags=tags,
            source=entry.sources[0] if entry.sources else "discovery",
            notes=None,
            is_active=payload.is_active,
            allow_privileged=payload.allow_privileged,
            ssh_target=
                entry.ssh_aliases[0]
                if entry.ssh_aliases
                else (entry.addresses[0] if entry.addresses else entry.hostname),
            last_seen_at=datetime.utcnow(),
        )
        session.add(host)
        session.commit()
        session.refresh(host)
        existing[key] = host
        imported.append(_host_to_schema(host))

    return imported


@router.get("/comparisons", response_model=list[ComparisonMetric])
def comparison_metrics(
    hosts: list[int] = Query(default_factory=list),
    categories: list[str] = Query(default_factory=list),
    session: Session = Depends(get_session),
) -> list[ComparisonMetric]:
    if not hosts:
        return []

    category_filter = {cat for cat in categories if cat in COMPARISON_CATEGORIES}
    if not category_filter:
        category_filter = set(COMPARISON_CATEGORIES.keys()) - {"software"}

    db_hosts = (
        session.exec(select(models.Host).where(models.Host.id.in_(hosts))).all()
        if hosts
        else []
    )
    host_lookup = {host.id: host for host in db_hosts}

    metrics: list[ComparisonMetric] = []
    for host_id in hosts:
        host = host_lookup.get(host_id)
        if not host:
            continue

        report, payload = _latest_report_with_payload(session, host.id)
        metrics_data = payload.get("metrics", {}) if payload else {}
        ratings_data = payload.get("ratings", {}) if payload else {}
        storage_hint = payload.get("storage_hint") if payload else None
        tips = payload.get("tips", []) if payload else []

        def append_metric(category: str, label: str, value: str | float | int | None, hint: str | None = None) -> None:
            if category in category_filter:
                metrics.append(
                    ComparisonMetric(
                        host_id=host.id,
                        category=category,
                        label=label,
                        value=value,
                        hint=hint,
                    )
                )

        if not payload:
            append_metric(
                "overview",
                "Status",
                "No assessment",
                "Trigger an assessment to capture hardware metrics.",
            )
            continue

        ram_total = metrics_data.get("ram_total_gb")
        ram_max = metrics_data.get("ram_max_capacity_gb")
        ram_empty = metrics_data.get("ram_empty")
        storage_total = metrics_data.get("storage_total")
        storage_nvme = metrics_data.get("storage_nvme")
        cpu_model = metrics_data.get("cpu_model", "Unknown")
        cores = metrics_data.get("cores")
        threads = metrics_data.get("threads")
        cpu_max = metrics_data.get("cpu_max_ghz")
        gpu_has = metrics_data.get("has_dedicated_gpu")
        gpu_vram = metrics_data.get("gpu_vram_gb")
        virtualization = metrics_data.get("virtualization") or "Unknown"

        overview_value = f"{cpu_model} — {threads or '?'} threads, {ram_total:.1f} GB RAM" if isinstance(ram_total, (int, float)) else f"{cpu_model}"
        overview_hint = ratings_data.get("Developer workstation", {}).get("summary") if ratings_data else None
        if not overview_hint and tips:
            overview_hint = tips[0]
        append_metric("overview", "Profile", overview_value, overview_hint)

        if isinstance(ram_total, (int, float)):
            memory_value = f"{ram_total:.1f} GB"
            if isinstance(ram_max, (int, float)):
                memory_value += f" / {ram_max:.0f} GB max"
        else:
            memory_value = "Unknown"
        memory_hint = None
        if isinstance(ram_empty, int):
            memory_hint = f"Empty slots: {ram_empty}"
        append_metric("memory", "Installed vs Max", memory_value, memory_hint)

        storage_value = f"{storage_total or 0} devices"
        if storage_nvme is not None:
            storage_value += f" (NVMe {storage_nvme})"
        append_metric("storage", "Storage", storage_value, storage_hint)

        cpu_value = f"{cpu_model}"
        if cores is not None and threads is not None:
            cpu_value += f" — {cores} cores / {threads} threads"
        if isinstance(cpu_max, (int, float)) and cpu_max > 0:
            cpu_value += f" up to {cpu_max:.2f} GHz"
        append_metric("cpu", "CPU", cpu_value, virtualization if virtualization != "Unknown" else None)

        if gpu_has:
            if isinstance(gpu_vram, (int, float)) and gpu_vram:
                gpu_value = f"Discrete ({gpu_vram:.1f} GB VRAM)"
            else:
                gpu_value = "Discrete"
            gpu_hint = ratings_data.get("LLM / ML", {}).get("summary") if ratings_data else None
        else:
            gpu_value = "Integrated / none"
            gpu_hint = "Add a discrete GPU for heavier workloads." if ratings_data else None
        append_metric("gpu", "GPU", gpu_value, gpu_hint)

        append_metric("software", "Inventory", "Planned", "Software inventory capture scheduled for a future sprint.")

    return metrics


@router.post("/hosts", response_model=HostRead, status_code=status.HTTP_201_CREATED)
def create_host(payload: HostCreate, session: Session = Depends(get_session)) -> HostRead:
    host = session.exec(select(models.Host).where(models.Host.hostname == payload.hostname)).first()
    if host:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Host with this hostname already exists")

    db_host = models.Host(
        hostname=payload.hostname,
        address=payload.address,
        tags=_tags_to_string(payload.tags),
        source=payload.source,
        notes=payload.notes,
        is_active=payload.is_active if payload.is_active is not None else True,
        allow_privileged=payload.allow_privileged if payload.allow_privileged is not None else True,
        ssh_target=payload.ssh_target or payload.address or payload.hostname,
        last_seen_at=datetime.utcnow(),
    )
    session.add(db_host)
    session.commit()
    session.refresh(db_host)

    return _host_to_schema(db_host)


@router.patch("/hosts/{host_id}", response_model=HostRead)
def update_host(host_id: int, payload: HostUpdate, session: Session = Depends(get_session)) -> HostRead:
    host = session.get(models.Host, host_id)
    if not host:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Host not found")

    if payload.address is not None:
        host.address = payload.address
    if payload.tags is not None:
        host.tags = _tags_to_string(payload.tags)
    if payload.source is not None:
        host.source = payload.source
    if payload.notes is not None:
        host.notes = payload.notes
    if payload.is_active is not None:
        host.is_active = payload.is_active
    if payload.allow_privileged is not None:
        host.allow_privileged = payload.allow_privileged
    if payload.ssh_target is not None:
        host.ssh_target = payload.ssh_target

    session.add(host)
    session.commit()
    session.refresh(host)
    return _host_to_schema(host)


def _run_assessment(job_id: int) -> None:
    with session_scope() as session:
        job = session.get(models.AssessmentJob, job_id)
        if not job:
            return
        host = session.get(models.Host, job.host_id)
        if not host:
            job.status = "error"
            job.error_message = "Host record missing"
            job.finished_at = datetime.utcnow()
            session.add(job)
            session.commit()
            return

        host_snapshot = models.Host.model_validate(host)
        job.status = "running"
        job.started_at = datetime.utcnow()
        job.error_message = None
        session.add(job)
        session.commit()

    try:
        report_data = _collect_assessment_for_host(host_snapshot)
    except Exception as exc:  # pylint: disable=broad-except
        with session_scope() as session:
            job = session.get(models.AssessmentJob, job_id)
            if not job:
                return
            job.status = "error"
            job.error_message = str(exc)
            job.finished_at = datetime.utcnow()
            session.add(job)
            session.commit()
        return

    markdown = report_data.get("markdown", "")
    raw_payload = json.dumps(report_data)

    with session_scope() as session:
        job = session.get(models.AssessmentJob, job_id)
        if not job:
            return
        job.status = "completed"
        job.finished_at = datetime.utcnow()
        job.error_message = None
        session.add(job)

        report = models.Report(
            job_id=job.id,
            rendered_markdown=markdown,
            raw_payload=raw_payload,
        )
        session.add(report)

        host = session.get(models.Host, job.host_id)
        if host:
            host.last_seen_at = datetime.utcnow()
            session.add(host)

        session.commit()


@router.post("/jobs", response_model=JobRead, status_code=status.HTTP_202_ACCEPTED)
def create_job(
    payload: JobCreate,
    background_tasks: BackgroundTasks,
    session: Session = Depends(get_session),
) -> JobRead:
    host = session.get(models.Host, payload.host_id)
    if not host:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Host not found")

    job = models.AssessmentJob(host_id=host.id)
    session.add(job)
    session.commit()
    session.refresh(job)

    background_tasks.add_task(_run_assessment, job.id)
    return _job_to_schema(job)


@router.get("/jobs", response_model=list[JobRead])
def list_jobs(session: Session = Depends(get_session)) -> list[JobRead]:
    jobs = session.exec(select(models.AssessmentJob).order_by(models.AssessmentJob.requested_at.desc())).all()
    return [_job_to_schema(job) for job in jobs]


@router.get("/jobs/{job_id}", response_model=JobRead)
def get_job(job_id: int, session: Session = Depends(get_session)) -> JobRead:
    job = session.get(models.AssessmentJob, job_id)
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")
    return _job_to_schema(job)


@router.get("/reports/{job_id}", response_model=ReportRead)
def get_report(job_id: int, session: Session = Depends(get_session)) -> ReportRead:
    report = session.exec(select(models.Report).where(models.Report.job_id == job_id)).first()
    if not report:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Report not found")
    return _report_to_schema(report)
