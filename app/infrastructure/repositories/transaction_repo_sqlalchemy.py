from __future__ import annotations

from collections.abc import Callable
from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, Numeric, String, select
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column

from app.domain.models import Money, Transaction, TransactionType
from app.domain.repositories import TransactionRepository


class Base(DeclarativeBase):
    pass


class TransactionORM(Base):
    __tablename__ = "transactions"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    user_id: Mapped[str] = mapped_column(String, nullable=False, index=True)
    type: Mapped[str] = mapped_column(String, nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False)
    occurred_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, index=True
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    category_id: Mapped[str | None] = mapped_column(String, nullable=True, index=True)
    account_id: Mapped[str | None] = mapped_column(String, nullable=True, index=True)
    description: Mapped[str | None] = mapped_column(String(500), nullable=True)


class SQLAlchemyTransactionRepository(TransactionRepository):
    def __init__(self, *, session_factory: Callable[[], Session]) -> None:
        self._session_factory = session_factory

    def add(self, tx: Transaction) -> None:
        # Domain -> DB conversion
        row = TransactionORM(
            id=tx.id,
            user_id=tx.user_id,
            type=tx.type.value,
            amount=tx.money.amount,
            currency=tx.money.currency,
            occurred_at=tx.occurred_at,
            created_at=tx.created_at,
            category_id=tx.category_id,
            account_id=tx.account_id,
            description=tx.description,
        )
        with self._session_factory() as session:
            session.add(row)
            session.commit()

    def get(self, transaction_id: str) -> Transaction | None:
        with self._session_factory() as session:
            row = session.get(TransactionORM, transaction_id)
            if row is None:
                return None
            # DB -> Domain conversion
            return self._to_domain(row)

    def list_by_user(self, user_id: str) -> list[Transaction]:
        with self._session_factory() as session:
            stmt = (
                select(TransactionORM)
                .where(TransactionORM.user_id == user_id)
                .order_by(TransactionORM.created_at.desc())
            )
            rows = session.execute(stmt).scalars().all()
            return [self._to_domain(row) for row in rows]

    def list_by_user_and_categories(
        self,
        *,
        user_id: str,
        category_ids: list[str],
    ) -> list[Transaction]:
        if not category_ids:
            return []
        with self._session_factory() as session:
            stmt = (
                select(TransactionORM)
                .where(TransactionORM.user_id == user_id)
                .where(TransactionORM.category_id.in_(category_ids))
                .order_by(TransactionORM.created_at.desc())
            )
            rows = session.execute(stmt).scalars().all()
            return [self._to_domain(row) for row in rows]

    def list_by_user_and_period(
        self,
        *,
        user_id: str,
        start_at: datetime,
        end_at: datetime,
    ) -> list[Transaction]:
        with self._session_factory() as session:
            stmt = (
                select(TransactionORM)
                .where(TransactionORM.user_id == user_id)
                .where(TransactionORM.occurred_at >= start_at)
                .where(TransactionORM.occurred_at <= end_at)
                .order_by(TransactionORM.occurred_at.desc())
            )
            rows = session.execute(stmt).scalars().all()
            return [self._to_domain(row) for row in rows]

    @staticmethod
    def _to_domain(row: TransactionORM) -> Transaction:
        return Transaction(
            id=row.id,
            user_id=row.user_id,
            type=TransactionType(row.type),
            money=Money(amount=row.amount, currency=row.currency),
            occurred_at=row.occurred_at,
            created_at=row.created_at,
            category_id=row.category_id,
            account_id=row.account_id,
            description=row.description,
        )
