from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime

from app.domain.models import Transaction


class TransactionRepository(ABC):
    @abstractmethod
    def add(self, tx: Transaction) -> None: ...

    @abstractmethod
    def get(self, transaction_id: str) -> Transaction | None: ...

    @abstractmethod
    def list_by_user(self, user_id: str) -> list[Transaction]: ...

    @abstractmethod
    def list_by_user_and_categories(
        self,
        *,
        user_id: str,
        category_ids: list[str],
    ) -> list[Transaction]: ...

    @abstractmethod
    def list_by_user_and_period(
        self,
        *,
        user_id: str,
        start_at: datetime,
        end_at: datetime,
    ) -> list[Transaction]: ...
