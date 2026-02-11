from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.api.schemas.transactions import (
    CategoryExpenseResponse,
    TransactionCreateRequest,
    TransactionResponse,
    TransactionsByCategoriesResponse,
    TransactionsPeriodStatsResponse,
)
from app.application.services.transaction_service import TransactionService
from app.domain.errors import DomainValidationError, NotFoundError
from app.domain.models import Transaction
from app.infrastructure.db import get_session_factory
from app.infrastructure.repositories.transaction_repo_sqlalchemy import (
    SQLAlchemyTransactionRepository,
)

router = APIRouter(tags=["transactions"])


def get_transaction_service() -> TransactionService:
    session_factory = get_session_factory()
    repo = SQLAlchemyTransactionRepository(session_factory=session_factory)
    return TransactionService(repo=repo)


def _to_response(tx: Transaction) -> TransactionResponse:
    return TransactionResponse(
        id=tx.id,
        user_id=tx.user_id,
        type=tx.type.value,
        amount=tx.money.amount,
        currency=tx.money.currency,
        occurred_at=tx.occurred_at,
        category_id=tx.category_id,
        account_id=tx.account_id,
        description=tx.description,
        created_at=tx.created_at,
    )


@router.post(
    "/transactions",
    response_model=TransactionResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_transaction(
    request: TransactionCreateRequest,
    service: TransactionService = Depends(get_transaction_service),
) -> TransactionResponse:
    # In a real app, user_id would come from auth
    user_id = "demo-user"
    try:
        tx = service.record_transaction(
            user_id=user_id,
            tx_type=request.type,
            amount=request.amount,
            currency=request.currency,
            occurred_at=request.occurred_at,
            category_id=request.category_id,
            account_id=request.account_id,
            description=request.description,
        )
    except DomainValidationError as e:
        raise HTTPException(status_code=422, detail=str(e)) from e

    return _to_response(tx)


@router.get("/transactions", response_model=list[TransactionResponse])
def list_transactions(
    service: TransactionService = Depends(get_transaction_service),
) -> list[TransactionResponse]:
    user_id = "demo-user"
    transactions = service.list_transactions(user_id=user_id)
    return [_to_response(tx) for tx in transactions]


@router.get(
    "/transactions/by-categories",
    response_model=TransactionsByCategoriesResponse,
)
def list_transactions_by_categories(
    category_ids: list[str] = Query(
        ..., description="Repeat query param: ?category_ids=food&category_ids=transport"
    ),
    service: TransactionService = Depends(get_transaction_service),
) -> TransactionsByCategoriesResponse:
    user_id = "demo-user"
    try:
        transactions, total_expense, expense_by_category = service.get_transactions_by_categories(
            user_id=user_id,
            category_ids=category_ids,
        )
    except DomainValidationError as e:
        raise HTTPException(status_code=422, detail=str(e)) from e

    return TransactionsByCategoriesResponse(
        transactions=[_to_response(tx) for tx in transactions],
        total_expense=total_expense,
        expense_by_category=[
            CategoryExpenseResponse(category_id=category_id, total_expense=total)
            for category_id, total in expense_by_category.items()
        ],
    )


@router.get(
    "/transactions/by-period",
    response_model=TransactionsPeriodStatsResponse,
)
def list_transactions_by_period(
    start_at: datetime,
    end_at: datetime,
    service: TransactionService = Depends(get_transaction_service),
) -> TransactionsPeriodStatsResponse:
    user_id = "demo-user"
    try:
        transactions, total_expense, expense_by_category = service.get_transactions_for_period(
            user_id=user_id,
            start_at=start_at,
            end_at=end_at,
        )
    except DomainValidationError as e:
        raise HTTPException(status_code=422, detail=str(e)) from e

    return TransactionsPeriodStatsResponse(
        start_at=start_at,
        end_at=end_at,
        transactions=[_to_response(tx) for tx in transactions],
        total_expense=total_expense,
        expense_by_category=[
            CategoryExpenseResponse(category_id=category_id, total_expense=total)
            for category_id, total in expense_by_category.items()
        ],
    )


@router.get("/transactions/{transaction_id}", response_model=TransactionResponse)
def get_transaction(
    transaction_id: str,
    service: TransactionService = Depends(get_transaction_service),
) -> TransactionResponse:
    user_id = "demo-user"
    try:
        tx = service.get_transaction(user_id=user_id, transaction_id=transaction_id)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e

    return _to_response(tx)
