from fastapi.testclient import TestClient

import app.models
from app.api import routes
from app.main import app
from app.models.base import Base

client = TestClient(app)


def test_liveness_endpoint() -> None:
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_database_health_endpoint_with_mocked_connection(monkeypatch) -> None:
    def fake_check_database_connection() -> tuple[bool, str]:
        return True, "Database connection ok"

    monkeypatch.setattr(
        routes, "check_database_connection", fake_check_database_connection
    )

    response = client.get("/api/health/database")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "detail": "Database connection ok"}


def test_mapped_tables_registered() -> None:
    expected_tables = {"customers", "employees", "orders", "products"}
    assert expected_tables.issubset(set(Base.metadata.tables.keys()))
