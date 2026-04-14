# Laborit Project

## 🇧🇷 Português (PT-BR)

### Visão geral

API em FastAPI para um Copiloto Comercial, com foco em:

- orquestração previsível;
- resiliência (retry, timeout e circuit breaker);
- observabilidade (trace e metadados por etapa);
- facilidade de manutenção com arquitetura modular.

O projeto usa **Poetry** para dependências e **SQLAlchemy** para acesso a dados.

---

### Estrutura do projeto

```text
project/
├── app/
│   ├── main.py
│   ├── api/
│   │   └── routes.py
│   ├── domain/
│   │   ├── __init__.py
│   │   └── query.py
│   ├── orchestrator/
│   │   ├── orchestrator.py
│   │   ├── resilience.py
│   │   └── metadata.py
│   ├── services/
│   │   ├── query_service.py
│   │   ├── data_service.py
│   │   └── llm_service.py
│   ├── builder/
│   │   └── response_builder.py
│   ├── models/
│   └── utils/
├── tests/
└── README.md
```

---

### Endpoints disponíveis

- `GET /api/health`
- `GET /api/health/database`
- `POST /api/copilot/question`

---

### Setup e execução

#### 1) Instalação

```bash
poetry install
```

#### 2) Rodar API

```bash
poetry run uvicorn app.main:app --reload
```

#### 3) Rodar testes

```bash
poetry run pytest -q
```

#### 4) Rodar cobertura

```bash
poetry run pytest --cov=app --cov-report=term-missing -q
```

---

### Fluxo da requisição (detalhado)

1. A API valida a pergunta recebida.
2. O `Orchestrator` cria contexto da requisição (`trace_id`, timers, steps).
3. O `response_cache` é consultado primeiro (atalho mais rápido).
4. Em cache miss, `QueryService` transforma texto em `QueryPlan`.
5. O `data_cache` é consultado por intent/entidade/operação/limite.
6. Em cache miss, `DataService` busca dados no banco com engine resiliente.
7. O `LLMService` gera texto final a partir dos dados estruturados.
8. Em erro de dados/LLM, o fluxo usa fallback amigável.
9. `ResponseBuilder` entrega `message + metadata` para o endpoint.

---

### Arquitetura e responsabilidades

#### `app/domain/query.py`

- `QueryIntent` (`Enum`): fonte única dos intents permitidos.
- `QueryPlan` (`dataclass`): contrato entre interpretação de pergunta e consulta de dados.
- `data_cache_key()`: centraliza estratégia de chave de cache de dados.

#### `app/services/query_service.py`

- Converte linguagem natural em `QueryPlan`.
- Não fala com banco nem com LLM.

#### `app/services/data_service.py`

- Executa consultas SQLAlchemy com base no `QueryPlan`.
- Retorna payload estruturado para a camada de geração de texto.

#### `app/services/llm_service.py`

- Converte dados estruturados em resposta textual.
- Também produz texto de fallback em cenários degradados.

#### `app/orchestrator/resilience.py`

- `run_step()`: mede e registra tempo/status por etapa.
- `run_with_resilience()`: encapsula retry + timeout + circuit breaker.

#### `app/orchestrator/metadata.py`

- `build_request_metadata()`: contrato único de metadados da resposta.

#### `app/orchestrator/orchestrator.py`

- Coordena o fluxo ponta a ponta.
- Mantém regras de sequência e decisões (cache/live/fallback).
- Delega detalhes técnicos para módulos especializados.

---

### Decisões arquiteturais (e por quê)

1. **Enum para intent (`QueryIntent`)**
	- Evita strings soltas e erros de digitação.
	- Melhora autocomplete e legibilidade nas comparações.

2. **`QueryPlan` como contrato formal**
	- Cria fronteira clara entre interpretação (`QueryService`) e execução (`DataService`).
	- Facilita teste isolado por camada.

3. **Resiliência extraída para módulo próprio**
	- Remove complexidade técnica do `Orchestrator`.
	- Permite evoluir retry/timeout/circuit breaker sem mexer na regra de negócio.

4. **Metadata centralizada**
	- Mudanças no contrato observável ocorrem em um único ponto.
	- Garante consistência entre respostas com e sem fallback.

5. **Orchestrator como coordenador (não executor técnico)**
	- Fica menor, mais previsível e mais fácil de manter.
	- Aumenta clareza do fluxo para onboarding de novos devs.

6. **Fallback amigável por padrão**
	- Prioriza experiência do usuário em falhas parciais.
	- Evita retornar erro técnico cru para o consumidor da API.

---

### Contrato de resposta

`POST /api/copilot/question` retorna:

- `answer`: texto final para o usuário;
- `metadata.trace_id`: ID de correlação da requisição;
- `metadata.intent`: intent detectado;
- `metadata.cache`: status de cache (`response_cache` / `data_cache`);
- `metadata.steps`: telemetria por etapa;
- `metadata.fallback_used`: indicador de resposta degradada;
- `metadata.total_duration_ms`: duração total do fluxo.

---

### Banco de dados

- Engine: MySQL (`mysql+pymysql`)
- Banco alvo: `northwind`
- Tabelas mapeadas: `customers`, `employees`, `orders`, `products`

Prioridade de configuração:

1. `DATABASE_URL`
2. `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT`, `DB_NAME`

Boas práticas:

- nunca hardcode de credenciais;
- sempre usar variáveis de ambiente;
- mensagens de erro de conexão não devem vazar DSN/senha.

---

### Qualidade e testes

- Testes unitários e de fluxo cobrem serviços, orquestração e endpoints.
- Cobertura atual de referência nesta task: **99%** no pacote `app`.
- Comando oficial de cobertura:

```bash
poetry run pytest --cov=app --cov-report=term-missing -q
```

---

## 🇺🇸 English (EN)

### Overview

FastAPI-based Commercial Copilot API focused on:

- predictable orchestration;
- resilience (retry, timeout, circuit breaker);
- observability (trace + per-step metadata);
- maintainability through modular architecture.

Dependencies are managed with **Poetry**, and persistence uses **SQLAlchemy**.

---

### Project structure

```text
project/
├── app/
│   ├── main.py
│   ├── api/routes.py
│   ├── domain/query.py
│   ├── orchestrator/
│   │   ├── orchestrator.py
│   │   ├── resilience.py
│   │   └── metadata.py
│   ├── services/
│   │   ├── query_service.py
│   │   ├── data_service.py
│   │   └── llm_service.py
│   ├── builder/response_builder.py
│   ├── models/
│   └── utils/
├── tests/
└── README.md
```

---

### Available endpoints

- `GET /api/health`
- `GET /api/health/database`
- `POST /api/copilot/question`

---

### Setup and run

```bash
poetry install
poetry run uvicorn app.main:app --reload
poetry run pytest -q
poetry run pytest --cov=app --cov-report=term-missing -q
```

---

### Request flow

1. API validates input.
2. `Orchestrator` initializes request context.
3. Check `response_cache` first.
4. On miss, `QueryService` builds a `QueryPlan`.
5. Check `data_cache` using plan-based cache key.
6. On miss, `DataService` fetches data with resilient execution.
7. `LLMService` builds the final user-facing answer.
8. If data/LLM fails, fallback text is returned.
9. `ResponseBuilder` returns `message + metadata`.

---

### Architecture decisions (why)

1. **Intent enum (`QueryIntent`)**
	- Prevents typo-prone raw-string intent handling.
	- Improves type safety and readability.

2. **`QueryPlan` as a formal domain contract**
	- Clear boundary between NLP interpretation and data execution.
	- Easier isolated testing.

3. **Dedicated resilience module**
	- Keeps orchestration logic clean.
	- Centralizes retry/timeout/circuit-breaker behavior.

4. **Dedicated metadata builder**
	- Single place for response metadata schema.
	- Consistent observability output across all paths.

5. **Orchestrator as coordinator only**
	- Better separation of concerns.
	- Lower cognitive load and easier evolution.

6. **Friendly fallback as default failure strategy**
	- Better user experience in partial outages.
	- Avoids exposing low-level technical errors.

---

### Response contract

`POST /api/copilot/question` returns:

- `answer`
- `metadata.trace_id`
- `metadata.intent`
- `metadata.cache`
- `metadata.steps`
- `metadata.fallback_used`
- `metadata.total_duration_ms`

---

### Database

- MySQL via `mysql+pymysql`
- Target database: `northwind`
- Mapped tables: `customers`, `employees`, `orders`, `products`

Configuration priority:

1. `DATABASE_URL`
2. `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT`, `DB_NAME`

Security notes:

- never hardcode credentials;
- use environment variables;
- do not leak DSN/password in error responses.
