from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal
from enum import Enum
from uuid import uuid4

from app.domain.errors import DomainValidationError


class TransactionType(str, Enum):
    expense = "expense"
    income = "income"


@dataclass(frozen=True, slots=True)
class Money:
    amount: Decimal
    currency: str

    def __post_init__(self) -> None:
        if self.amount <= 0:
            raise DomainValidationError("Amount must be greater than 0")
        if not self.currency or len(self.currency) != 3:
            raise DomainValidationError("Currency must be a 3-letter code (e.g. RUB)")


@dataclass(frozen=True, slots=True)
class Transaction:
    id: str
    user_id: str
    type: TransactionType
    money: Money
    occurred_at: datetime
    created_at: datetime
    category_id: str | None = None
    account_id: str | None = None
    description: str | None = None

    @staticmethod
    def create(
        *,
        user_id: str,
        type: TransactionType,
        money: Money,
        occurred_at: datetime,
        category_id: str | None,
        account_id: str | None,
        description: str | None,
    ) -> Transaction:
        if not user_id:
            raise DomainValidationError("user_id is required")
        if occurred_at.tzinfo is None:
            # For simplicity: require timezone-aware timestamps.
            # Alternative: treat naive datetime as UTC.
            raise DomainValidationError("occurred_at must be timezone-aware (e.g. UTC)")

        now = datetime.now(tz=UTC)
        return Transaction(
            id=str(uuid4()),
            user_id=user_id,
            type=type,
            money=money,
            occurred_at=occurred_at,
            created_at=now,
            category_id=category_id,
            account_id=account_id,
            description=description,
        )
