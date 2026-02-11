from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.infrastructure.repositories.transaction_repo_sqlalchemy import Base

_engine: Engine | None = None
_session_factory: sessionmaker[Session] | None = None


def init_db(database_url: str | None = None) -> None:
    """
    Initialize SQLAlchemy engine/sessionmaker once at application startup.
    """
    global _engine, _session_factory
    if _engine is not None and _session_factory is not None:
        return

    if database_url is None:
        data_dir = Path("data")
        data_dir.mkdir(parents=True, exist_ok=True)
        db_path = data_dir / "app.db"
        database_url = f"sqlite:///{db_path}"

    _engine = create_engine(database_url, future=True)
    Base.metadata.create_all(bind=_engine)
    _session_factory = sessionmaker(
        bind=_engine,
        autocommit=False,
        autoflush=False,
        future=True,
    )


def get_session_factory() -> Callable[[], Session]:
    """
    Return initialized session factory.
    """
    if _session_factory is None:
        raise RuntimeError("Database is not initialized. Call init_db() at startup.")
    return _session_factory


def shutdown_db() -> None:
    """
    Dispose singleton engine/sessionmaker at application shutdown.
    """
    global _engine, _session_factory
    if _engine is not None:
        _engine.dispose()
    _engine = None
    _session_factory = None
