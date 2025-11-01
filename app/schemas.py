"""Pydantic models for API input/output."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class HostCreate(BaseModel):
    hostname: str
    address: Optional[str] = None
    tags: Optional[list[str]] = None


class HostRead(BaseModel):
    id: int
    hostname: str
    address: Optional[str]
    tags: list[str]
    last_seen_at: Optional[datetime]
    created_at: datetime

    class Config:
        from_attributes = True


class JobCreate(BaseModel):
    host_id: int


class JobRead(BaseModel):
    id: int
    host_id: int
    status: str
    requested_at: datetime
    started_at: Optional[datetime]
    finished_at: Optional[datetime]
    error_message: Optional[str]

    class Config:
        from_attributes = True


class ReportRead(BaseModel):
    id: int
    job_id: int
    rendered_markdown: str
    raw_payload: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True
