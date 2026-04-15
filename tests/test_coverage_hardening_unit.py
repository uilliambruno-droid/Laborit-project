import time

import pytest
from sqlalchemy import create_engine
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

import app.utils.database as database_module
from app.domain.query import QueryIntent, QueryPlan
from app.models.base import Base
from app.models.customer import Customer
from app.models.employee import Employee
from app.models.order import Order
from app.models.product import Product
from app.orchestrator.resilience import run_with_resilience
from app.services.data_service import DataService
from app.services.llm_service import LLMService
from app.services.query_service import QueryService
from app.utils.cache import InMemoryTTLCache
from app.utils.circuit_breaker import CircuitBreaker, CircuitBreakerOpenError


def create_test_session_factory() -> sessionmaker:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine, autoflush=False, autocommit=False)

    with factory() as session:
        session.add_all(
            [
                Customer(
                    customer_id="ALFKI",
                    company_name="Alfreds Futterkiste",
                    contact_name="Maria Anders",
                    country="Germany",
                ),
                Employee(
                    employee_id=1,
                    first_name="Nancy",
                    last_name="Davolio",
                    title="Sales Representative",
                ),
                Order(order_id=1, customer_id="ALFKI", employee_id=1),
                Product(
                    product_id=1,
                    product_name="Chai",
                    units_in_stock=39,
                    unit_price=18.0,
                ),
            ]
        )
        session.commit()

    return factory


def test_query_service_maps_employee_and_default_overview() -> None:
    service = QueryService()

    employee_plan = service.build_query("how many employees do we have?")
    default_plan = service.build_query("tell me about accounts")

    assert employee_plan.intent == QueryIntent.COUNT_EMPLOYEES
    assert default_plan.intent == QueryIntent.CUSTOMER_OVERVIEW


def test_llm_service_covers_remaining_generate_paths() -> None:
    service = LLMService()

    employees_text = service.generate_text(
        "employees?",
        {"intent": "count_employees", "total": 7},
    )
    orders_text = service.generate_text(
        "orders?",
        {"intent": "count_orders", "total": 11},
    )
    empty_stock_text = service.generate_text(
        "stock",
        {"intent": "top_products_by_stock", "records": []},
    )
    overview_empty_text = service.generate_text(
        "overview",
        {"intent": "customer_overview", "records": []},
    )
    overview_text = service.generate_text(
        "overview",
        {
            "intent": "customer_overview",
            "records": [
                {"company_name": "A"},
                {"company_name": "B"},
            ],
        },
    )

    assert "7 employees" in employees_text
    assert "11 orders" in orders_text
    assert "No products were found" in empty_stock_text
    assert "No customer data was found" in overview_empty_text
    assert "A, B" in overview_text


def test_llm_service_covers_fallback_paths() -> None:
    service = LLMService()

    no_data = service.generate_fallback_text("question", None)
    count_fallback = service.generate_fallback_text(
        "question",
        {"intent": "count_orders", "total": 3, "entity": "orders"},
    )
    list_fallback = service.generate_fallback_text(
        "question",
        {"intent": "customer_overview", "records": [{"id": 1}, {"id": 2}]},
    )
    generic_fallback = service.generate_fallback_text(
        "hello",
        {"intent": "customer_overview", "records": []},
    )
    pt_no_data = service.generate_fallback_text("Ola, tudo bem contigo?", None)

    assert "request was received" in no_data
    assert "3 orders" in count_fallback
    assert "2 records" in list_fallback
    assert "We received the question 'hello'" in generic_fallback
    assert "solicitação foi recebida" in pt_no_data


def test_data_service_customer_overview_branch() -> None:
    service = DataService(session_factory=create_test_session_factory())
    plan = QueryPlan(
        intent=QueryIntent.CUSTOMER_OVERVIEW,
        entity="customers",
        operation="list",
        limit=5,
    )

    result = service.fetch_data(plan)

    assert result["intent"] == "customer_overview"
    assert isinstance(result["records"], list)
    assert result["records"][0]["company_name"] == "Alfreds Futterkiste"


def test_run_with_resilience_timeout_path() -> None:
    breaker = CircuitBreaker(name="timeout-breaker")
    steps: list[dict[str, object]] = []

    def slow_executor() -> str:
        time.sleep(0.03)
        return "ok"

    with pytest.raises(RuntimeError):
        run_with_resilience(
            breaker=breaker,
            timeout_seconds=0.001,
            retry_attempts=1,
            steps=steps,
            step_name="slow-step",
            executor=slow_executor,
        )

    assert steps[0]["status"] == "timeout"


def test_run_with_resilience_circuit_open_path() -> None:
    breaker = CircuitBreaker(name="open-breaker")
    breaker.state = "open"
    breaker.opened_at = None
    steps: list[dict[str, object]] = []

    with pytest.raises(RuntimeError):
        run_with_resilience(
            breaker=breaker,
            timeout_seconds=0.1,
            retry_attempts=1,
            steps=steps,
            step_name="blocked-step",
            executor=lambda: "never",
        )

    assert steps[0]["status"] == "circuit-open"


def test_circuit_breaker_before_call_and_recovery(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    breaker = CircuitBreaker(
        name="cb", failure_threshold=2, recovery_timeout_seconds=30
    )

    with pytest.raises(CircuitBreakerOpenError):
        breaker.state = "open"
        breaker.opened_at = None
        breaker.before_call()

    breaker.opened_at = 100.0
    monkeypatch.setattr("app.utils.circuit_breaker.monotonic", lambda: 105.0)
    with pytest.raises(CircuitBreakerOpenError):
        breaker.before_call()

    monkeypatch.setattr("app.utils.circuit_breaker.monotonic", lambda: 140.0)
    breaker.before_call()
    assert breaker.state == "half-open"

    breaker.record_success()
    assert breaker.state == "closed"
    assert breaker.failure_count == 0


def test_circuit_breaker_record_failure_opens() -> None:
    breaker = CircuitBreaker(name="cb", failure_threshold=2)

    breaker.record_failure()
    assert breaker.state == "closed"
    breaker.record_failure()

    snapshot = breaker.snapshot()
    assert snapshot.state == "open"
    assert snapshot.failure_count == 2


def test_cache_expiration_and_clear() -> None:
    cache = InMemoryTTLCache[int](ttl_seconds=0)
    cache.set("a", 1)

    assert cache.get("a") is None

    cache = InMemoryTTLCache[int](ttl_seconds=60)
    cache.set("a", 1)
    cache.clear()
    assert cache.get("a") is None


def test_database_url_branches_and_engine_creation(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    database_module.get_engine.cache_clear()

    monkeypatch.setenv("DATABASE_URL", "sqlite+pysqlite:///:memory:")
    assert database_module.get_database_url() == "sqlite+pysqlite:///:memory:"

    database_module.get_engine.cache_clear()
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.setenv("DB_USER", "u")
    monkeypatch.setenv("DB_PASSWORD", "p")
    monkeypatch.setenv("DB_HOST", "h")
    monkeypatch.setenv("DB_NAME", "n")
    monkeypatch.setenv("DB_PORT", "3307")
    built = database_module.get_database_url()
    assert built == "mysql+pymysql://u:p@h:3307/n"

    calls: list[str] = []

    def fake_create_engine(url: str, **_: object) -> str:
        calls.append(url)
        return "ENGINE"

    database_module.get_engine.cache_clear()
    monkeypatch.setattr("app.utils.database.create_engine", fake_create_engine)
    assert database_module.get_engine() == "ENGINE"
    assert calls


def test_database_check_connection_error_paths(monkeypatch: pytest.MonkeyPatch) -> None:
    class FailingRuntimeEngine:
        def connect(self):
            raise RuntimeError("missing env")

    class FailingSqlAlchemyEngine:
        def connect(self):
            raise SQLAlchemyError("db down")

    monkeypatch.setattr("app.utils.database.get_engine", lambda: FailingRuntimeEngine())
    ok, detail = database_module.check_database_connection()
    assert ok is False
    assert "not configured" in detail

    monkeypatch.setattr(
        "app.utils.database.get_engine", lambda: FailingSqlAlchemyEngine()
    )
    ok, detail = database_module.check_database_connection()
    assert ok is False
    assert detail == "Database connection failed"
