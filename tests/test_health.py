from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_liveness_endpoint() -> None:
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_copilot_question_route_returns_answer() -> None:
    response = client.post(
        "/api/copilot/question",
        json={"question": "Which customers need attention this week?"},
    )
    assert response.status_code == 200
    assert "answer" in response.json()


def test_copilot_question_route_validates_payload() -> None:
    response = client.post("/api/copilot/question", json={"question": "ok"})
    assert response.status_code == 422
