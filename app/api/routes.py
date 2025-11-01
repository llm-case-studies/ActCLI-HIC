"""API routes for the Hardware Insight Console."""

from __future__ import annotations

from datetime import datetime
from typing import Iterable

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from sqlmodel import Session, select

from .. import models, discovery
from ..db import get_session, init_db, session_scope
from ..schemas import (
    HostCreate,
    HostRead,
    HostUpdate,
    HostDiscovery,
    HostCheckRequest,
    HostCheckResponse,
    JobCreate,
    JobRead,
    ReportRead,
)

router = APIRouter()


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


@router.on_event("startup")
def startup_event() -> None:
    init_db()


@router.get("/hosts", response_model=list[HostRead])
def list_hosts(session: Session = Depends(get_session)) -> list[HostRead]:
    hosts = session.exec(select(models.Host)).all()
    return [_host_to_schema(host) for host in hosts]


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

    session.add(host)
    session.commit()
    session.refresh(host)
    return _host_to_schema(host)


def _run_assessment(job_id: int) -> None:
    """Placeholder job runner until SSH integration is implemented."""

    with session_scope() as session:
        job = session.get(models.AssessmentJob, job_id)
        if not job:
            return
        host = session.get(models.Host, job.host_id)
        job.status = "running"
        job.started_at = datetime.utcnow()
        session.add(job)
        session.commit()
        session.refresh(job)

        # TODO: integrate SSH execution of hw_assessor here.
        job.status = "completed"
        job.finished_at = datetime.utcnow()
        session.add(job)

        privileged_note = ""
        if host and not host.allow_privileged:
            privileged_note = "\n\n_note: Privileged probes were skipped (sudo disabled for this host)._"

        report = models.Report(
            job_id=job.id,
            rendered_markdown="Assessment pending implementation." + privileged_note,
            raw_payload=None,
        )
        session.add(report)
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
