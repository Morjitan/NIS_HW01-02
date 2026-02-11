from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.routes.transactions import router as transactions_router
from app.infrastructure.db import init_db, shutdown_db


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    init_db()
    yield
    shutdown_db()


def create_app() -> FastAPI:
    app = FastAPI(title="Expense Tracker API", version="0.1.0", lifespan=lifespan)

    # Observability hook:
    # - Here we can add middleware for request logging, metrics (Prometheus), and tracing (OpenTelemetry).
    # - Example: add a middleware that records latency and status code per endpoint.

    app.include_router(transactions_router, prefix="/api")
    return app


app = create_app()
