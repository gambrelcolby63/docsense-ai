"""SQLAlchemy engine setup that accepts SQLite or Postgres URLs."""

from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import sessionmaker


def normalize_database_url(database_url: str) -> str:
    """Accept the postgres:// URL some hosts paste, and select the psycopg driver."""
    url = database_url.strip()
    if url.startswith("postgres://"):
        url = "postgresql://" + url.removeprefix("postgres://")
    if url.startswith("postgresql://"):
        url = "postgresql+psycopg://" + url.removeprefix("postgresql://")
    return url


def database_kind(database_url: str) -> str:
    normalized = normalize_database_url(database_url)
    if normalized.startswith("postgresql"):
        return "postgres"
    return "sqlite"


def make_engine(database_url: str) -> Engine:
    url = normalize_database_url(database_url)
    connect_args: dict = {}
    if url.startswith("sqlite"):
        _ensure_sqlite_directory(url)
        connect_args["check_same_thread"] = False
    return create_engine(url, connect_args=connect_args)


def make_session_factory(engine: Engine) -> sessionmaker:
    return sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)


def _ensure_sqlite_directory(database_url: str) -> None:
    # sqlite:///./data/app.db  -> ./data/app.db
    # sqlite:////data/app.db   -> /data/app.db
    # sqlite:///:memory:       -> keep the default in-memory database
    if not database_url.startswith("sqlite:///"):
        return
    raw_path = database_url.removeprefix("sqlite:///")
    if raw_path in {":memory:", ""} or raw_path.startswith("file:"):
        return
    path = Path(raw_path)
    if path.parent and str(path.parent) not in {"", "."}:
        path.parent.mkdir(parents=True, exist_ok=True)
