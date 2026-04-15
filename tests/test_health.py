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


def test_database_health_missing_env_vars_returns_safe_message(monkeypatch) -> None:
    """When required env vars are absent the response must NOT expose credentials or DSN."""
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.delenv("DB_USER", raising=False)
    monkeypatch.delenv("DB_PASSWORD", raising=False)
    monkeypatch.delenv("DB_HOST", raising=False)
    monkeypatch.delenv("DB_NAME", raising=False)

    # Also clear the lru_cache so get_engine() re-evaluates with missing vars
    import app.utils.database as db_module

    db_module.get_engine.cache_clear()

    response = client.get("/api/health/database")
    data = response.json()

    # Must never expose host, user, password or the full DSN
    assert "DB_PASSWORD" not in str(data)
    assert "laborit" not in str(data).lower()
    assert "northwind-mysql-db" not in str(data)
    assert data["status"] == "unavailable"


def test_copilot_question_endpoint_success() -> None:
    class FakeOrchestrator:
        def run(self, user_input: str) -> dict[str, object]:
            return {
                "message": f"mocked answer for: {user_input}",
                "metadata": {
                    "trace_id": "trace-123",
                    "response_source": "generated",
                    "fallback_used": False,
                },
            }

    routes.orchestrator = FakeOrchestrator()

    response = client.post(
        "/api/copilot/question",
        json={"question": "Which customers should I prioritize this week?"},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload == {
        "answer": "mocked answer for: Which customers should I prioritize this week?",
        "metadata": {
            "trace_id": "trace-123",
            "response_source": "generated",
            "fallback_used": False,
        },
    }


def test_copilot_question_endpoint_rejects_blank_question() -> None:
    class FakeOrchestrator:
        def run(self, user_input: str) -> dict[str, object]:
            return {"message": f"mocked answer for: {user_input}", "metadata": {}}

    routes.orchestrator = FakeOrchestrator()

    response = client.post("/api/copilot/question", json={"question": "     "})
    assert response.status_code == 422


def test_copilot_question_endpoint_rejects_extra_fields() -> None:
    class FakeOrchestrator:
        def run(self, user_input: str) -> dict[str, object]:
            return {"message": f"mocked answer for: {user_input}", "metadata": {}}

    routes.orchestrator = FakeOrchestrator()

    response = client.post(
        "/api/copilot/question",
        json={"question": "How many active clients do I have?", "debug": True},
    )
    assert response.status_code == 422


def test_copilot_question_endpoint_returns_friendly_validation_payload() -> None:
    response = client.post("/api/copilot/question", json={"question": "Hi"})

    assert response.status_code == 422
    payload = response.json()
    assert (
        payload["message"] == "Invalid request payload. Check the fields and try again."
    )
    assert (
        payload["message_pt"] == "Payload inválido. Revise os campos e tente novamente."
    )
    assert payload["errors"][0]["field"] == "question"
    assert "at least 5 characters" in payload["errors"][0]["message"]


def test_copilot_question_requires_api_key_when_configured(monkeypatch) -> None:
    class FakeOrchestrator:
        def run(self, user_input: str) -> dict[str, object]:
            return {"message": f"mocked answer for: {user_input}", "metadata": {}}

    routes.orchestrator = FakeOrchestrator()
    monkeypatch.setenv("API_KEY", "secret-key")

    unauthorized = client.post(
        "/api/copilot/question",
        json={"question": "How many customers do we have?"},
    )
    assert unauthorized.status_code == 401

    authorized = client.post(
        "/api/copilot/question",
        json={"question": "How many customers do we have?"},
        headers={"X-API-Key": "secret-key"},
    )
    assert authorized.status_code == 200


def test_metrics_endpoint_security_and_response(monkeypatch) -> None:
    monkeypatch.setenv("API_KEY", "metrics-key")

    unauthorized = client.get("/api/metrics")
    assert unauthorized.status_code == 401

    authorized = client.get("/api/metrics", headers={"X-API-Key": "metrics-key"})
    assert authorized.status_code == 200
    payload = authorized.json()
    assert "http" in payload
    assert "copilot" in payload
