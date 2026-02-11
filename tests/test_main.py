from __future__ import annotations

from fastapi.testclient import TestClient
from starlette.routing import Route

from app.main import create_app


def test_create_app_has_expected_metadata_and_routes() -> None:
    app = create_app()
    assert app.title == "Expense Tracker API"
    assert app.version == "0.1.0"
    paths = {route.path for route in app.routes if isinstance(route, Route)}
    assert "/api/transactions" in paths
    assert "/api/transactions/{transaction_id}" in paths
    assert "/api/transactions/by-categories" in paths
    assert "/api/transactions/by-period" in paths


def test_docs_endpoint_is_available() -> None:
    with TestClient(create_app()) as client:
        response = client.get("/docs")
    assert response.status_code == 200


def test_root_is_not_implemented_for_mvp() -> None:
    with TestClient(create_app()) as client:
        response = client.get("/")
    assert response.status_code == 404
