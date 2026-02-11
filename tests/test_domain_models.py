from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal

import pytest

from app.domain.errors import DomainValidationError
from app.domain.models import Money, Transaction, TransactionType


def test_money_rejects_zero_amount() -> None:
    with pytest.raises(DomainValidationError, match="Amount must be greater than 0"):
        Money(amount=Decimal("0"), currency="RUB")


def test_money_rejects_invalid_currency() -> None:
    with pytest.raises(DomainValidationError, match="Currency must be a 3-letter code"):
        Money(amount=Decimal("1"), currency="RU")


def test_transaction_create_requires_user_id() -> None:
    with pytest.raises(DomainValidationError, match="user_id is required"):
        Transaction.create(
            user_id="",
            type=TransactionType.expense,
            money=Money(amount=Decimal("1"), currency="RUB"),
            occurred_at=datetime(2026, 1, 1, tzinfo=UTC),
            category_id=None,
            account_id=None,
            description=None,
        )


def test_transaction_create_requires_timezone_aware_datetime() -> None:
    with pytest.raises(DomainValidationError, match="occurred_at must be timezone-aware"):
        Transaction.create(
            user_id="u1",
            type=TransactionType.expense,
            money=Money(amount=Decimal("1"), currency="RUB"),
            occurred_at=datetime(2026, 1, 1),
            category_id=None,
            account_id=None,
            description=None,
        )


def test_transaction_create_success() -> None:
    tx = Transaction.create(
        user_id="u1",
        type=TransactionType.income,
        money=Money(amount=Decimal("15.50"), currency="RUB"),
        occurred_at=datetime(2026, 1, 1, tzinfo=UTC),
        category_id="salary",
        account_id="card",
        description="salary",
    )

    assert tx.id
    assert tx.user_id == "u1"
    assert tx.type == TransactionType.income
    assert tx.money.amount == Decimal("15.50")
    assert tx.created_at.tzinfo is not None
