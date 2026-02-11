from datetime import UTC, datetime
from decimal import Decimal

import pytest

from app.application.services.transaction_service import TransactionService
from app.domain.errors import DomainValidationError, NotFoundError
from app.domain.models import Transaction
from app.domain.repositories import TransactionRepository


class InMemoryTransactionRepository(TransactionRepository):
    def __init__(self) -> None:
        self._items: dict[str, Transaction] = {}

    def add(self, tx: Transaction) -> None:
        self._items[tx.id] = tx

    def get(self, transaction_id: str) -> Transaction | None:
        return self._items.get(transaction_id)

    def list_by_user(self, user_id: str) -> list[Transaction]:
        return [tx for tx in self._items.values() if tx.user_id == user_id]

    def list_by_user_and_categories(
        self,
        *,
        user_id: str,
        category_ids: list[str],
    ) -> list[Transaction]:
        categories = set(category_ids)
        return [
            tx
            for tx in self._items.values()
            if tx.user_id == user_id and tx.category_id in categories
        ]

    def list_by_user_and_period(
        self,
        *,
        user_id: str,
        start_at: datetime,
        end_at: datetime,
    ) -> list[Transaction]:
        return [
            tx
            for tx in self._items.values()
            if tx.user_id == user_id and start_at <= tx.occurred_at <= end_at
        ]


def test_record_transaction_success() -> None:
    repo = InMemoryTransactionRepository()
    service = TransactionService(repo=repo)

    tx = service.record_transaction(
        user_id="u1",
        tx_type="expense",
        amount=Decimal("10.50"),
        currency="RUB",
        occurred_at=datetime(2026, 1, 22, 12, 0, tzinfo=UTC),
        category_id="food",
        account_id=None,
        description="lunch",
    )

    assert tx.id
    assert tx.user_id == "u1"
    assert tx.type.value == "expense"
    assert tx.money.amount == Decimal("10.50")
    assert repo.get(tx.id) is tx


def test_record_transaction_invalid_amount() -> None:
    repo = InMemoryTransactionRepository()
    service = TransactionService(repo=repo)

    with pytest.raises(DomainValidationError):
        service.record_transaction(
            user_id="u1",
            tx_type="expense",
            amount=Decimal("0"),
            currency="RUB",
            occurred_at=datetime(2026, 1, 22, 12, 0, tzinfo=UTC),
            category_id=None,
            account_id=None,
            description=None,
        )


def test_get_transaction_not_found() -> None:
    repo = InMemoryTransactionRepository()
    service = TransactionService(repo=repo)

    with pytest.raises(NotFoundError):
        service.get_transaction(user_id="u1", transaction_id="missing")


def test_get_transaction_forbidden_other_user() -> None:
    repo = InMemoryTransactionRepository()
    service = TransactionService(repo=repo)

    tx = service.record_transaction(
        user_id="u1",
        tx_type="income",
        amount=Decimal("100"),
        currency="RUB",
        occurred_at=datetime(2026, 1, 22, 12, 0, tzinfo=UTC),
        category_id=None,
        account_id=None,
        description=None,
    )

    with pytest.raises(NotFoundError):
        service.get_transaction(user_id="u2", transaction_id=tx.id)


def test_list_transactions_only_for_user() -> None:
    repo = InMemoryTransactionRepository()
    service = TransactionService(repo=repo)

    service.record_transaction(
        user_id="u1",
        tx_type="expense",
        amount=Decimal("50"),
        currency="RUB",
        occurred_at=datetime(2026, 1, 22, 12, 0, tzinfo=UTC),
        category_id=None,
        account_id=None,
        description="u1 tx",
    )
    service.record_transaction(
        user_id="u2",
        tx_type="income",
        amount=Decimal("70"),
        currency="RUB",
        occurred_at=datetime(2026, 1, 23, 12, 0, tzinfo=UTC),
        category_id=None,
        account_id=None,
        description="u2 tx",
    )

    transactions = service.list_transactions(user_id="u1")
    assert len(transactions) == 1
    assert transactions[0].user_id == "u1"


def test_get_transactions_by_categories_with_total_expense() -> None:
    repo = InMemoryTransactionRepository()
    service = TransactionService(repo=repo)

    service.record_transaction(
        user_id="u1",
        tx_type="expense",
        amount=Decimal("100"),
        currency="RUB",
        occurred_at=datetime(2026, 1, 10, 12, 0, tzinfo=UTC),
        category_id="food",
        account_id=None,
        description=None,
    )
    service.record_transaction(
        user_id="u1",
        tx_type="income",
        amount=Decimal("20"),
        currency="RUB",
        occurred_at=datetime(2026, 1, 11, 12, 0, tzinfo=UTC),
        category_id="food",
        account_id=None,
        description=None,
    )
    service.record_transaction(
        user_id="u1",
        tx_type="expense",
        amount=Decimal("50"),
        currency="RUB",
        occurred_at=datetime(2026, 1, 12, 12, 0, tzinfo=UTC),
        category_id="transport",
        account_id=None,
        description=None,
    )
    service.record_transaction(
        user_id="u1",
        tx_type="expense",
        amount=Decimal("200"),
        currency="RUB",
        occurred_at=datetime(2026, 1, 13, 12, 0, tzinfo=UTC),
        category_id="health",
        account_id=None,
        description=None,
    )
    service.record_transaction(
        user_id="u2",
        tx_type="expense",
        amount=Decimal("999"),
        currency="RUB",
        occurred_at=datetime(2026, 1, 14, 12, 0, tzinfo=UTC),
        category_id="food",
        account_id=None,
        description=None,
    )

    transactions, total_expense, expense_by_category = service.get_transactions_by_categories(
        user_id="u1",
        category_ids=["food", "transport"],
    )

    assert len(transactions) == 3
    assert total_expense == Decimal("150")
    assert expense_by_category["food"] == Decimal("100")
    assert expense_by_category["transport"] == Decimal("50")


def test_get_transactions_by_categories_empty_categories() -> None:
    repo = InMemoryTransactionRepository()
    service = TransactionService(repo=repo)

    with pytest.raises(DomainValidationError):
        service.get_transactions_by_categories(user_id="u1", category_ids=[])


def test_get_transactions_for_period_with_category_stats() -> None:
    repo = InMemoryTransactionRepository()
    service = TransactionService(repo=repo)

    service.record_transaction(
        user_id="u1",
        tx_type="expense",
        amount=Decimal("100"),
        currency="RUB",
        occurred_at=datetime(2026, 1, 5, 12, 0, tzinfo=UTC),
        category_id="food",
        account_id=None,
        description=None,
    )
    service.record_transaction(
        user_id="u1",
        tx_type="expense",
        amount=Decimal("40"),
        currency="RUB",
        occurred_at=datetime(2026, 1, 15, 12, 0, tzinfo=UTC),
        category_id="transport",
        account_id=None,
        description=None,
    )
    service.record_transaction(
        user_id="u1",
        tx_type="income",
        amount=Decimal("500"),
        currency="RUB",
        occurred_at=datetime(2026, 1, 20, 12, 0, tzinfo=UTC),
        category_id="salary",
        account_id=None,
        description=None,
    )
    service.record_transaction(
        user_id="u1",
        tx_type="expense",
        amount=Decimal("80"),
        currency="RUB",
        occurred_at=datetime(2026, 2, 1, 12, 0, tzinfo=UTC),
        category_id="food",
        account_id=None,
        description=None,
    )

    transactions, total_expense, expense_by_category = service.get_transactions_for_period(
        user_id="u1",
        start_at=datetime(2026, 1, 1, 0, 0, tzinfo=UTC),
        end_at=datetime(2026, 1, 31, 23, 59, tzinfo=UTC),
    )

    assert len(transactions) == 3
    assert total_expense == Decimal("140")
    assert expense_by_category["food"] == Decimal("100")
    assert expense_by_category["transport"] == Decimal("40")
    assert "salary" not in expense_by_category


def test_get_transactions_for_period_invalid_range() -> None:
    repo = InMemoryTransactionRepository()
    service = TransactionService(repo=repo)

    with pytest.raises(DomainValidationError):
        service.get_transactions_for_period(
            user_id="u1",
            start_at=datetime(2026, 2, 1, 0, 0, tzinfo=UTC),
            end_at=datetime(2026, 1, 1, 0, 0, tzinfo=UTC),
        )
