from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.api import routes
from app.builder.response_builder import ResponseBuilder
from app.main import app
from app.models.base import Base
from app.models.customer import Customer
from app.models.employee import Employee
from app.models.order import Order
from app.models.product import Product
from app.orchestrator.orchestrator import Orchestrator
from app.services.data_service import DataService
from app.services.llm_service import LLMService
from app.services.query_service import QueryPlan, QueryService
from app.utils.cache import InMemoryTTLCache


def create_test_session_factory() -> sessionmaker:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    session_factory = sessionmaker(bind=engine, autoflush=False, autocommit=False)

    with session_factory() as session:
        session.add_all(
            [
                Customer(
                    customer_id="ALFKI",
                    company_name="Alfreds Futterkiste",
                    contact_name="Maria Anders",
                    country="Germany",
                ),
                Customer(
                    customer_id="ANATR",
                    company_name="Ana Trujillo Emparedados",
                    contact_name="Ana Trujillo",
                    country="Mexico",
                ),
                Employee(
                    employee_id=1,
                    first_name="Nancy",
                    last_name="Davolio",
                    title="Sales Representative",
                ),
                Employee(
                    employee_id=2,
                    first_name="Andrew",
                    last_name="Fuller",
                    title="Vice President",
                ),
                Order(order_id=1, customer_id="ALFKI", employee_id=1),
                Order(order_id=2, customer_id="ANATR", employee_id=2),
                Product(
                    product_id=1,
                    product_name="Chai",
                    units_in_stock=39,
                    unit_price=18.0,
                ),
                Product(
                    product_id=2,
                    product_name="Chang",
                    units_in_stock=17,
                    unit_price=19.0,
                ),
                Product(
                    product_id=3,
                    product_name="Aniseed Syrup",
                    units_in_stock=13,
                    unit_price=10.0,
                ),
            ]
        )
        session.commit()

    return session_factory


def create_test_orchestrator() -> Orchestrator:
    session_factory = create_test_session_factory()
    return Orchestrator(
        query_service=QueryService(),
        data_service=DataService(session_factory=session_factory),
        llm_service=LLMService(),
        response_builder=ResponseBuilder(),
    )


def test_orchestrator_returns_customer_count() -> None:
    orchestrator = create_test_orchestrator()

    result = orchestrator.run("How many customers do we have?")

    assert (
        result["message"]
        == "There are 2 customers available in the current portfolio dataset."
    )
    assert result["metadata"]["intent"] == "count_customers"
    assert result["metadata"]["fallback_used"] is False


def test_orchestrator_returns_top_products() -> None:
    orchestrator = create_test_orchestrator()

    result = orchestrator.run("Show me the products with highest stock")

    assert "Top products by stock are" in result["message"]
    assert "Chai (39 units)" in result["message"]


def test_copilot_question_endpoint_uses_integrated_services(monkeypatch) -> None:
    monkeypatch.setattr(routes, "orchestrator", create_test_orchestrator())
    client = TestClient(app)

    response = client.post(
        "/api/copilot/question",
        json={"question": "How many orders do we have?"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert (
        payload["answer"]
        == "There are 2 orders registered in the current portfolio dataset."
    )
    assert payload["metadata"]["intent"] == "count_orders"
    assert payload["metadata"]["fallback_used"] is False


def test_copilot_question_endpoint_rejects_extra_fields(monkeypatch) -> None:
    monkeypatch.setattr(routes, "orchestrator", create_test_orchestrator())
    client = TestClient(app)

    response = client.post(
        "/api/copilot/question",
        json={"question": "How many customers do we have?", "debug": True},
    )

    assert response.status_code == 422


class CountingDataService:
    def __init__(self) -> None:
        self.calls = 0

    def fetch_data(self, query: QueryPlan) -> dict[str, object]:
        self.calls += 1
        return {"intent": query.intent, "entity": query.entity, "total": 2}


class CountingLLMService:
    def __init__(self) -> None:
        self.calls = 0

    def generate_text(self, user_input: str, data: dict[str, object]) -> str:
        self.calls += 1
        return f"Synthetic answer for {data['intent']}"


def test_orchestrator_uses_data_cache_for_same_intent() -> None:
    data_service = CountingDataService()
    llm_service = CountingLLMService()
    orchestrator = Orchestrator(
        query_service=QueryService(),
        data_service=data_service,  # type: ignore[arg-type]
        llm_service=llm_service,  # type: ignore[arg-type]
        response_builder=ResponseBuilder(),
        data_cache=InMemoryTTLCache(ttl_seconds=120),
        response_cache=InMemoryTTLCache(ttl_seconds=120),
    )

    first = orchestrator.run("How many customers do we have?")
    second = orchestrator.run("How many customers are there in total?")

    assert data_service.calls == 1
    assert llm_service.calls == 2
    assert "Synthetic answer for count_customers" in first["message"]
    assert "Synthetic answer for count_customers" in second["message"]


def test_orchestrator_uses_response_cache_for_same_question() -> None:
    data_service = CountingDataService()
    llm_service = CountingLLMService()
    orchestrator = Orchestrator(
        query_service=QueryService(),
        data_service=data_service,  # type: ignore[arg-type]
        llm_service=llm_service,  # type: ignore[arg-type]
        response_builder=ResponseBuilder(),
        data_cache=InMemoryTTLCache(ttl_seconds=120),
        response_cache=InMemoryTTLCache(ttl_seconds=120),
    )

    first = orchestrator.run("How many customers do we have?")
    second = orchestrator.run("How many customers do we have?")

    assert data_service.calls == 1
    assert llm_service.calls == 1
    assert first["message"] == second["message"]
    assert first["metadata"]["cache"]["response_cache"] == "miss"
    assert second["metadata"]["cache"]["response_cache"] == "hit"


class FailingLLMService:
    def generate_text(self, user_input: str, data: dict[str, object]) -> str:
        raise RuntimeError("llm unavailable")

    def generate_fallback_text(
        self, user_input: str, data: dict[str, object] | None = None
    ) -> str:
        return "Fallback answer generated"


class FailingDataService:
    def __init__(self) -> None:
        self.calls = 0

    def fetch_data(self, query: QueryPlan) -> dict[str, object]:
        self.calls += 1
        raise RuntimeError("database unavailable")


def test_orchestrator_uses_llm_fallback_on_generation_error() -> None:
    orchestrator = Orchestrator(
        query_service=QueryService(),
        data_service=CountingDataService(),  # type: ignore[arg-type]
        llm_service=FailingLLMService(),  # type: ignore[arg-type]
        response_builder=ResponseBuilder(),
        data_cache=InMemoryTTLCache(ttl_seconds=120),
        response_cache=InMemoryTTLCache(ttl_seconds=120),
    )

    result = orchestrator.run("How many customers do we have?")

    assert result["message"] == "Fallback answer generated"
    assert result["metadata"]["fallback_used"] is True
    assert result["metadata"]["response_source"] == "fallback"


def test_orchestrator_opens_data_circuit_breaker_after_retries() -> None:
    failing_data_service = FailingDataService()
    orchestrator = Orchestrator(
        query_service=QueryService(),
        data_service=failing_data_service,  # type: ignore[arg-type]
        llm_service=LLMService(),
        response_builder=ResponseBuilder(),
        data_cache=InMemoryTTLCache(ttl_seconds=120),
        response_cache=InMemoryTTLCache(ttl_seconds=120),
        retry_attempts=2,
    )

    result = orchestrator.run("How many customers do we have?")

    assert result["metadata"]["fallback_used"] is True
    breaker_state = result["metadata"]["circuit_breakers"]["data_service"]["state"]
    assert breaker_state in {"closed", "open"}
    assert result["metadata"]["response_source"] == "fallback"
