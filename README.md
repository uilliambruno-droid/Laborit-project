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

## Database integration

Database connection is now implemented with SQLAlchemy + MySQL driver.

- Database engine: MySQL
- Database name: `northwind`
- Mapped tables: `customers`, `employees`, `orders`, `products`

Connection source priority:

1. `DATABASE_URL`
2. Individual vars: `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT`, `DB_NAME`

Important: use environment variables for credentials and never hardcode secrets in source files.
