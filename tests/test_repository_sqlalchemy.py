from __future__ import annotations

from collections.abc import Generator
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path

import pytest

from app.domain.models import Money, Transaction, TransactionType
from app.infrastructure.db import get_session_factory, init_db, shutdown_db
from app.infrastructure.repositories.transaction_repo_sqlalchemy import (
    SQLAlchemyTransactionRepository,
)


@pytest.fixture
def repo(tmp_path: Path) -> Generator[SQLAlchemyTransactionRepository, None, None]:
    shutdown_db()
    db_url = f"sqlite:///{tmp_path / 'repository.db'}"
    init_db(db_url)
    repository = SQLAlchemyTransactionRepository(session_factory=get_session_factory())
    yield repository
    shutdown_db()


def _build_tx(
    *,
    user_id: str,
    tx_type: TransactionType,
    amount: str,
    occurred_at: datetime,
    category_id: str | None,
) -> Transaction:
    return Transaction.create(
        user_id=user_id,
        type=tx_type,
        money=Money(amount=Decimal(amount), currency="RUB"),
        occurred_at=occurred_at,
        category_id=category_id,
        account_id=None,
        description="repo test",
    )


def test_repository_add_and_get(repo: SQLAlchemyTransactionRepository) -> None:
    tx = _build_tx(
        user_id="u1",
        tx_type=TransactionType.expense,
        amount="123.45",
        occurred_at=datetime(2026, 1, 1, tzinfo=UTC),
        category_id="food",
    )
    repo.add(tx)

    saved = repo.get(tx.id)
    assert saved is not None
    assert saved.id == tx.id
    assert saved.user_id == "u1"
    assert saved.money.amount == Decimal("123.45")
    assert repo.get("missing-id") is None


def test_repository_list_by_user(repo: SQLAlchemyTransactionRepository) -> None:
    tx1 = _build_tx(
        user_id="u1",
        tx_type=TransactionType.expense,
        amount="10.00",
        occurred_at=datetime(2026, 1, 1, tzinfo=UTC),
        category_id="food",
    )
    tx2 = _build_tx(
        user_id="u1",
        tx_type=TransactionType.income,
        amount="20.00",
        occurred_at=datetime(2026, 1, 2, tzinfo=UTC),
        category_id="salary",
    )
    tx3 = _build_tx(
        user_id="u2",
        tx_type=TransactionType.expense,
        amount="30.00",
        occurred_at=datetime(2026, 1, 3, tzinfo=UTC),
        category_id="food",
    )

    repo.add(tx1)
    repo.add(tx2)
    repo.add(tx3)

    result = repo.list_by_user("u1")
    assert len(result) == 2
    assert {tx.user_id for tx in result} == {"u1"}


def test_repository_list_by_user_and_categories(repo: SQLAlchemyTransactionRepository) -> None:
    repo.add(
        _build_tx(
            user_id="u1",
            tx_type=TransactionType.expense,
            amount="10.00",
            occurred_at=datetime(2026, 1, 1, tzinfo=UTC),
            category_id="food",
        )
    )
    repo.add(
        _build_tx(
            user_id="u1",
            tx_type=TransactionType.expense,
            amount="15.00",
            occurred_at=datetime(2026, 1, 2, tzinfo=UTC),
            category_id="transport",
        )
    )
    repo.add(
        _build_tx(
            user_id="u1",
            tx_type=TransactionType.expense,
            amount="25.00",
            occurred_at=datetime(2026, 1, 3, tzinfo=UTC),
            category_id="health",
        )
    )

    selected = repo.list_by_user_and_categories(user_id="u1", category_ids=["food", "transport"])
    assert len(selected) == 2
    assert {tx.category_id for tx in selected} == {"food", "transport"}

    assert repo.list_by_user_and_categories(user_id="u1", category_ids=[]) == []


def test_repository_list_by_user_and_period(repo: SQLAlchemyTransactionRepository) -> None:
    repo.add(
        _build_tx(
            user_id="u1",
            tx_type=TransactionType.expense,
            amount="10.00",
            occurred_at=datetime(2026, 1, 1, 10, 0, tzinfo=UTC),
            category_id="food",
        )
    )
    repo.add(
        _build_tx(
            user_id="u1",
            tx_type=TransactionType.expense,
            amount="15.00",
            occurred_at=datetime(2026, 1, 15, 10, 0, tzinfo=UTC),
            category_id="transport",
        )
    )
    repo.add(
        _build_tx(
            user_id="u1",
            tx_type=TransactionType.expense,
            amount="20.00",
            occurred_at=datetime(2026, 2, 1, 10, 0, tzinfo=UTC),
            category_id="health",
        )
    )

    period = repo.list_by_user_and_period(
        user_id="u1",
        start_at=datetime(2026, 1, 1, 0, 0, tzinfo=UTC),
        end_at=datetime(2026, 1, 31, 23, 59, tzinfo=UTC),
    )

    assert len(period) == 2
    assert all(tx.occurred_at.month == 1 for tx in period)
