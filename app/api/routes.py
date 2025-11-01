"""API routes for the Hardware Insight Console."""

from __future__ import annotations

from datetime import datetime
from typing import Iterable

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from sqlmodel import Session, select

from .. import models
from ..db import get_session, init_db, session_scope
from ..schemas import HostCreate, HostRead, JobCreate, JobRead, ReportRead

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


@router.post("/hosts", response_model=HostRead, status_code=status.HTTP_201_CREATED)
def create_host(payload: HostCreate, session: Session = Depends(get_session)) -> HostRead:
    host = session.exec(select(models.Host).where(models.Host.hostname == payload.hostname)).first()
    if host:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Host with this hostname already exists")

    db_host = models.Host(
        hostname=payload.hostname,
        address=payload.address,
        tags=_tags_to_string(payload.tags),
        last_seen_at=datetime.utcnow(),
    )
    session.add(db_host)
    session.commit()
    session.refresh(db_host)

    return _host_to_schema(db_host)


def _run_assessment(job_id: int) -> None:
    """Placeholder job runner until SSH integration is implemented."""

    with session_scope() as session:
        job = session.get(models.AssessmentJob, job_id)
        if not job:
            return
        job.status = "running"
        job.started_at = datetime.utcnow()
        session.add(job)
        session.commit()
        session.refresh(job)

        # TODO: integrate SSH execution of hw_assessor here.
        job.status = "completed"
        job.finished_at = datetime.utcnow()
        session.add(job)

        report = models.Report(
            job_id=job.id,
            rendered_markdown="Assessment pending implementation.",
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
