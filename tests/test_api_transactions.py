from __future__ import annotations

from collections.abc import Generator
from datetime import datetime
from decimal import Decimal
from typing import Any, cast

import pytest
from fastapi.testclient import TestClient

from app.api.routes.transactions import get_transaction_service
from app.application.services.transaction_service import TransactionService
from app.domain.errors import DomainValidationError
from app.domain.models import Transaction
from app.domain.repositories import TransactionRepository
from app.main import create_app


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


@pytest.fixture
def test_client() -> Generator[TestClient, None, None]:
    repo = InMemoryTransactionRepository()
    service = TransactionService(repo=repo)
    app = create_app()
    app.dependency_overrides[get_transaction_service] = lambda: service
    with TestClient(app) as client:
        yield client
    app.dependency_overrides.clear()


def _create_transaction(
    client: TestClient,
    *,
    tx_type: str,
    amount: str,
    occurred_at: str,
    category_id: str | None = None,
) -> dict[str, Any]:
    payload: dict[str, str | None] = {
        "type": tx_type,
        "amount": amount,
        "currency": "RUB",
        "occurred_at": occurred_at,
        "category_id": category_id,
        "description": "test transaction",
    }
    response = client.post("/api/transactions", json=payload)
    assert response.status_code == 201
    return cast(dict[str, Any], response.json())


def test_create_get_and_list_transactions(test_client: TestClient) -> None:
    first = _create_transaction(
        test_client,
        tx_type="expense",
        amount="100.00",
        occurred_at="2026-01-10T10:00:00Z",
        category_id="food",
    )
    _create_transaction(
        test_client,
        tx_type="income",
        amount="20.00",
        occurred_at="2026-01-11T10:00:00Z",
        category_id="salary",
    )

    get_response = test_client.get(f"/api/transactions/{first['id']}")
    assert get_response.status_code == 200
    assert get_response.json()["id"] == first["id"]

    list_response = test_client.get("/api/transactions")
    assert list_response.status_code == 200
    assert len(list_response.json()) == 2


def test_get_transaction_not_found_returns_404(test_client: TestClient) -> None:
    response = test_client.get("/api/transactions/missing-id")
    assert response.status_code == 404
    assert response.json()["detail"] == "Transaction not found"


def test_transactions_by_categories_returns_totals(test_client: TestClient) -> None:
    _create_transaction(
        test_client,
        tx_type="expense",
        amount="100.00",
        occurred_at="2026-01-10T10:00:00Z",
        category_id="food",
    )
    _create_transaction(
        test_client,
        tx_type="expense",
        amount="40.00",
        occurred_at="2026-01-11T10:00:00Z",
        category_id="transport",
    )
    _create_transaction(
        test_client,
        tx_type="income",
        amount="20.00",
        occurred_at="2026-01-12T10:00:00Z",
        category_id="food",
    )

    response = test_client.get(
        "/api/transactions/by-categories",
        params=[("category_ids", "food"), ("category_ids", "transport")],
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["total_expense"] == "140.00"
    by_category = {
        item["category_id"]: item["total_expense"] for item in payload["expense_by_category"]
    }
    assert by_category["food"] == "100.00"
    assert by_category["transport"] == "40.00"


def test_transactions_by_period_returns_totals(test_client: TestClient) -> None:
    _create_transaction(
        test_client,
        tx_type="expense",
        amount="100.00",
        occurred_at="2026-01-10T10:00:00Z",
        category_id="food",
    )
    _create_transaction(
        test_client,
        tx_type="expense",
        amount="40.00",
        occurred_at="2026-01-11T10:00:00Z",
        category_id="transport",
    )
    _create_transaction(
        test_client,
        tx_type="expense",
        amount="80.00",
        occurred_at="2026-02-01T10:00:00Z",
        category_id="food",
    )

    response = test_client.get(
        "/api/transactions/by-period",
        params={
            "start_at": "2026-01-01T00:00:00Z",
            "end_at": "2026-01-31T23:59:59Z",
        },
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["total_expense"] == "140.00"
    by_category = {
        item["category_id"]: item["total_expense"] for item in payload["expense_by_category"]
    }
    assert by_category["food"] == "100.00"
    assert by_category["transport"] == "40.00"


def test_transactions_by_period_invalid_range_returns_422(test_client: TestClient) -> None:
    response = test_client.get(
        "/api/transactions/by-period",
        params={
            "start_at": "2026-02-01T00:00:00Z",
            "end_at": "2026-01-01T00:00:00Z",
        },
    )
    assert response.status_code == 422
    assert response.json()["detail"] == "start_at must be before or equal to end_at"


def test_create_transaction_maps_domain_error_to_422() -> None:
    class BrokenService:
        def record_transaction(self, **_: object) -> None:
            raise DomainValidationError("forced domain error")

    app = create_app()
    app.dependency_overrides[get_transaction_service] = lambda: BrokenService()
    with TestClient(app) as client:
        response = client.post(
            "/api/transactions",
            json={
                "type": "expense",
                "amount": "1.00",
                "currency": "RUB",
                "occurred_at": "2026-01-10T10:00:00Z",
            },
        )
    app.dependency_overrides.clear()

    assert response.status_code == 422
    assert response.json()["detail"] == "forced domain error"


def test_transactions_by_categories_maps_domain_error_to_422() -> None:
    class BrokenService:
        def get_transactions_by_categories(
            self,
            *,
            user_id: str,
            category_ids: list[str],
        ) -> tuple[list[Transaction], Decimal, dict[str, Decimal]]:
            del user_id, category_ids
            raise DomainValidationError("forced category error")

    app = create_app()
    app.dependency_overrides[get_transaction_service] = lambda: BrokenService()
    with TestClient(app) as client:
        response = client.get(
            "/api/transactions/by-categories",
            params=[("category_ids", "food")],
        )
    app.dependency_overrides.clear()

    assert response.status_code == 422
    assert response.json()["detail"] == "forced category error"
