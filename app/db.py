"""Database utilities using SQLModel."""

from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

from sqlalchemy import text
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
    _maybe_upgrade_schema(engine)


def _maybe_upgrade_schema(engine) -> None:
    """Apply simple, idempotent schema migrations (SQLite only)."""

    if engine.url.get_backend_name() != "sqlite":
        return

    with engine.begin() as connection:
        columns = {
            row[1]
            for row in connection.execute(text("PRAGMA table_info('host')"))
        }
        if "source" not in columns:
            connection.execute(text("ALTER TABLE host ADD COLUMN source TEXT"))
        if "notes" not in columns:
            connection.execute(text("ALTER TABLE host ADD COLUMN notes TEXT"))
        if "is_active" not in columns:
            connection.execute(text("ALTER TABLE host ADD COLUMN is_active BOOLEAN DEFAULT 1"))
        if "allow_privileged" not in columns:
            connection.execute(text("ALTER TABLE host ADD COLUMN allow_privileged BOOLEAN DEFAULT 1"))


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
