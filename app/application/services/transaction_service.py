from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal

from app.domain.errors import DomainValidationError, NotFoundError
from app.domain.models import Money, Transaction, TransactionType
from app.domain.repositories import TransactionRepository


class TransactionService:
    def __init__(self, repo: TransactionRepository) -> None:
        self._repo = repo

    def record_transaction(
        self,
        *,
        user_id: str,
        tx_type: str,
        amount: Decimal,
        currency: str,
        occurred_at: datetime,
        category_id: str | None,
        account_id: str | None,
        description: str | None,
    ) -> Transaction:
        # Observability hook:
        # - add structured logging: event="RecordTransaction", user_id, amount, currency
        # - add metrics: counter transactions_created_total{type,currency}, histogram latency

        try:
            ttype = TransactionType(tx_type)
        except ValueError as e:
            raise DomainValidationError(f"Unsupported transaction type: {tx_type}") from e

        if occurred_at.tzinfo is None:
            occurred_at = occurred_at.replace(tzinfo=UTC)

        money = Money(amount=amount, currency=currency)
        tx = Transaction.create(
            user_id=user_id,
            type=ttype,
            money=money,
            occurred_at=occurred_at,
            category_id=category_id,
            account_id=account_id,
            description=description,
        )
        self._repo.add(tx)
        return tx

    def get_transaction(self, *, user_id: str, transaction_id: str) -> Transaction:
        # Observability hook:
        # - add structured logging: event="GetTransaction", user_id, transaction_id
        tx = self._repo.get(transaction_id)
        if tx is None or tx.user_id != user_id:
            raise NotFoundError("Transaction not found")
        return tx

    def list_transactions(self, *, user_id: str) -> list[Transaction]:
        return self._repo.list_by_user(user_id)

    def get_transactions_by_categories(
        self,
        *,
        user_id: str,
        category_ids: list[str],
    ) -> tuple[list[Transaction], Decimal, dict[str, Decimal]]:
        unique_category_ids = list(dict.fromkeys(category_ids))
        if not unique_category_ids:
            raise DomainValidationError("category_ids must not be empty")

        transactions = self._repo.list_by_user_and_categories(
            user_id=user_id,
            category_ids=unique_category_ids,
        )

        expense_by_category = {category_id: Decimal("0") for category_id in unique_category_ids}
        total_expense = Decimal("0")
        for tx in transactions:
            if tx.type == TransactionType.expense:
                total_expense += tx.money.amount
                if tx.category_id is not None:
                    expense_by_category[tx.category_id] = (
                        expense_by_category.get(tx.category_id, Decimal("0")) + tx.money.amount
                    )

        return transactions, total_expense, expense_by_category

    def get_transactions_for_period(
        self,
        *,
        user_id: str,
        start_at: datetime,
        end_at: datetime,
    ) -> tuple[list[Transaction], Decimal, dict[str | None, Decimal]]:
        start_at = self._normalize_datetime(start_at)
        end_at = self._normalize_datetime(end_at)
        if start_at > end_at:
            raise DomainValidationError("start_at must be before or equal to end_at")

        transactions = self._repo.list_by_user_and_period(
            user_id=user_id,
            start_at=start_at,
            end_at=end_at,
        )

        expense_by_category: dict[str | None, Decimal] = {}
        total_expense = Decimal("0")
        for tx in transactions:
            if tx.type == TransactionType.expense:
                total_expense += tx.money.amount
                expense_by_category[tx.category_id] = (
                    expense_by_category.get(tx.category_id, Decimal("0")) + tx.money.amount
                )

        return transactions, total_expense, expense_by_category

    @staticmethod
    def _normalize_datetime(value: datetime) -> datetime:
        if value.tzinfo is None:
            return value.replace(tzinfo=UTC)
        return value
