"""Database utilities using SQLModel."""

from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

from sqlmodel import Session, SQLModel, create_engine

from .config import get_settings


def _engine_url() -> str:
    settings = get_settings()
    db_url = settings.database_url
    if db_url.startswith("sqlite"):
        path = db_url.split("sqlite:///")[-1]
        Path(path).parent.mkdir(parents=True, exist_ok=True)
    return db_url


def get_engine(echo: bool = False):
    """Create a SQLModel engine with lazy initialization."""

    if not hasattr(get_engine, "_engine"):
        get_engine._engine = create_engine(_engine_url(), echo=echo, future=True)
    return get_engine._engine


def init_db() -> None:
    """Create database tables if they do not exist."""

    engine = get_engine()
    SQLModel.metadata.create_all(engine)


@contextmanager
def session_scope() -> Iterator[Session]:
    """Provide a transactional scope for DB operations."""

    engine = get_engine()
    with Session(engine) as session:
        yield session


def get_session() -> Iterator[Session]:
    """FastAPI dependency for acquiring a session."""

    engine = get_engine()
    with Session(engine) as session:
        yield session
