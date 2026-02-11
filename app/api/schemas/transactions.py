from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, Field


class TransactionCreateRequest(BaseModel):
    type: Literal["expense", "income"]
    amount: Decimal = Field(..., gt=0)
    currency: str = Field(default="RUB", min_length=3, max_length=3)
    occurred_at: datetime
    category_id: str | None = None
    account_id: str | None = None
    description: str | None = Field(default=None, max_length=500)


class TransactionResponse(BaseModel):
    id: str
    user_id: str
    type: Literal["expense", "income"]
    amount: Decimal
    currency: str
    occurred_at: datetime
    category_id: str | None
    account_id: str | None
    description: str | None
    created_at: datetime


class CategoryExpenseResponse(BaseModel):
    category_id: str | None
    total_expense: Decimal


class TransactionsByCategoriesResponse(BaseModel):
    transactions: list[TransactionResponse]
    total_expense: Decimal
    expense_by_category: list[CategoryExpenseResponse]


class TransactionsPeriodStatsResponse(BaseModel):
    start_at: datetime
    end_at: datetime
    transactions: list[TransactionResponse]
    total_expense: Decimal
    expense_by_category: list[CategoryExpenseResponse]
