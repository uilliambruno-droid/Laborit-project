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

## Database integration (next step)

The project is intentionally prepared as structure-first. Database integration will be added in the next task.

- Database engine: MySQL
- Database name: `northwind`
- Main tables to use first: `customers`, `employees`, `orders`, `products`

Important: use environment variables for credentials and never hardcode secrets in source files.
