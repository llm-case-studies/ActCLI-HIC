"""Database models for the Hardware Insight Console."""

from datetime import datetime
from typing import Optional

from sqlmodel import Field, SQLModel


class Host(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    hostname: str = Field(index=True)
    address: Optional[str] = Field(default=None, description="IPv4/IPv6 address")
    tags: Optional[str] = Field(default=None, description="Comma separated tags")
    last_seen_at: Optional[datetime] = Field(default=None)
    created_at: datetime = Field(default_factory=datetime.utcnow)


class AssessmentJob(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    host_id: int = Field(foreign_key="host.id")
    status: str = Field(default="queued", index=True)
    requested_at: datetime = Field(default_factory=datetime.utcnow)
    started_at: Optional[datetime] = Field(default=None)
    finished_at: Optional[datetime] = Field(default=None)
    error_message: Optional[str] = Field(default=None)


class Report(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    job_id: int = Field(foreign_key="assessmentjob.id", unique=True)
    rendered_markdown: str
    raw_payload: Optional[str] = Field(default=None, description="JSON payload or metadata")
    created_at: datetime = Field(default_factory=datetime.utcnow)
