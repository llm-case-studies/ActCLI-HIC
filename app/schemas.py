"""Pydantic models for API input/output."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class HostCreate(BaseModel):
    hostname: str
    address: Optional[str] = None
    tags: Optional[list[str]] = None
    source: Optional[str] = None
    notes: Optional[str] = None
    is_active: Optional[bool] = True
    allow_privileged: Optional[bool] = True


class HostRead(BaseModel):
    id: int
    hostname: str
    address: Optional[str]
    tags: list[str]
    source: Optional[str]
    notes: Optional[str]
    is_active: bool
    allow_privileged: bool
    last_seen_at: Optional[datetime]
    created_at: datetime

    class Config:
        from_attributes = True


class HostUpdate(BaseModel):
    address: Optional[str] = None
    tags: Optional[list[str]] = None
    source: Optional[str] = None
    notes: Optional[str] = None
    is_active: Optional[bool] = None
    allow_privileged: Optional[bool] = None


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


class HostDiscovery(BaseModel):
    hostname: str
    addresses: list[str] = Field(default_factory=list)
    sources: list[str] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)
    ssh_aliases: list[str] = Field(default_factory=list)
    known_host_id: Optional[int] = None
    is_active: Optional[bool] = None
    allow_privileged: Optional[bool] = None
    warnings: list[str] = Field(default_factory=list)


class HostCheckRequest(BaseModel):
    target: str
    timeout: Optional[int] = Field(default=5, ge=1, le=60)


class HostCheckResponse(BaseModel):
    target: str
    reachable: bool
    authenticated: bool
    returncode: int
    stdout: str
    stderr: str


class ComparisonMetric(BaseModel):
    host_id: int
    category: str
    label: str
    value: str | float | int | None
    hint: Optional[str] = None


class DiscoveryImportRequest(BaseModel):
    hostnames: list[str] = Field(default_factory=list)
    is_active: bool = True
    allow_privileged: bool = True
