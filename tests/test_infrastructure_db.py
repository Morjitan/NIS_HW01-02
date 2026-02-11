from __future__ import annotations

from pathlib import Path

import pytest

from app.infrastructure.db import get_session_factory, init_db, shutdown_db


def test_get_session_factory_requires_init() -> None:
    shutdown_db()
    with pytest.raises(RuntimeError, match="Database is not initialized"):
        get_session_factory()


def test_init_db_is_idempotent_and_shutdown_resets(tmp_path: Path) -> None:
    shutdown_db()
    db_url = f"sqlite:///{tmp_path / 'singleton.db'}"

    init_db(db_url)
    first_factory = get_session_factory()
    init_db(db_url)
    second_factory = get_session_factory()

    assert first_factory is second_factory

    shutdown_db()
    with pytest.raises(RuntimeError, match="Database is not initialized"):
        get_session_factory()


def test_shutdown_without_init_is_safe() -> None:
    shutdown_db()
    shutdown_db()
