# Laborit Project

Python project using FastAPI. Dependencies are managed with Poetry.

## Target structure

```text
project/
├── app/
│   ├── main.py
│   ├── api/
│   │   └── routes.py
│   ├── orchestrator/
│   │   └── orchestrator.py
│   ├── services/
│   │   ├── llm_service.py
│   │   ├── query_service.py
│   │   └── data_service.py
│   ├── builder/
│   │   └── response_builder.py
│   ├── models/
│   └── utils/
├── tests/
├── requirements.txt
└── README.md
```

## Setup

```bash
poetry install
```

## Run API

```bash
poetry run uvicorn app.main:app --reload
```

## Run tests

```bash
poetry run pytest
```

## Current endpoint

- `GET /api/health`
- `GET /api/health/database`
- `POST /api/copilot/question`

## Current request flow

The request path now includes orchestration, caching, resilience and transparency:

1. API validates the input question.
2. `Orchestrator` checks `response_cache` first.
3. If there is no cached response, `QueryService` builds a safe `QueryPlan`.
4. `Orchestrator` checks `data_cache` for the computed intent.
5. If needed, `DataService` queries the database through SQLAlchemy.
6. `LLMService` transforms structured data into the final answer.
7. `ResponseBuilder` returns the answer plus execution metadata.

## Resilience and observability

The current implementation already includes:

- in-memory TTL cache for response and data reuse;
- per-request `trace_id`;
- execution step timings;
- cache hit/miss metadata;
- circuit breaker state metadata for data and llm layers;
- retry + timeout handling inside the orchestrator;
- fallback response when data or llm generation fails.

### Response contract

`POST /api/copilot/question` returns:

- `answer`: final text shown to the user;
- `metadata.trace_id`: request correlation id;
- `metadata.intent`: detected business intent;
- `metadata.cache`: response/data cache status;
- `metadata.steps`: step-by-step execution timing;
- `metadata.fallback_used`: whether a degraded response was required.

## Database integration

Database connection is now implemented with SQLAlchemy + MySQL driver.

- Database engine: MySQL
- Database name: `northwind`
- Mapped tables: `customers`, `employees`, `orders`, `products`

Connection source priority:

1. `DATABASE_URL`
2. Individual vars: `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT`, `DB_NAME`

Important: use environment variables for credentials and never hardcode secrets in source files.
