# Operations Runbook

## PT-BR

### 1) Objetivo

Este runbook descreve como subir, validar e operar o `Laborit Project` em produção com segurança mínima, observabilidade e troubleshooting rápido.

### 2) Variáveis obrigatórias

- `DB_USER`
- `DB_PASSWORD`
- `DB_HOST`
- `DB_PORT` (default `3306`)
- `DB_NAME`

Alternativa: `DATABASE_URL` (tem prioridade)

### 3) Variáveis recomendadas para produção

- `CACHE_BACKEND=redis`
- `REDIS_URL=<redis-url>`
- `CACHE_PREFIX=laborit`
- `API_KEY=<segredo-forte>`

### 4) Comando de execução (Render)

Build:

```bash
poetry install --no-interaction --no-ansi
```

Start:

```bash
poetry run uvicorn app.main:app --host 0.0.0.0 --port $PORT --workers 2
```

Health check path:

```text
/api/health
```

### 5) Smoke tests pós-deploy

```bash
curl -s https://<service>.onrender.com/api/health
curl -s https://<service>.onrender.com/api/health/database
curl -s -H "X-API-Key: <API_KEY>" https://<service>.onrender.com/api/metrics
curl -s -X POST https://<service>.onrender.com/api/copilot/question \
  -H "Content-Type: application/json" \
  -H "X-API-Key: <API_KEY>" \
  -d '{"question":"How many customers do we have?"}'
```

### 6) Sinais de operação saudável

- `GET /api/health` retorna `{"status":"ok"}`.
- `GET /api/health/database` retorna `status: ok`.
- `GET /api/metrics` mostra crescimento de `http.requests_total`.
- `fallback_total` permanece baixo na maior parte do tempo.
- hit rate de cache aumenta após aquecimento.

### 7) Troubleshooting rápido

- `Database connection failed`:
  - validar `DB_*`/`DATABASE_URL`;
  - validar conectividade de rede entre app e banco.
- `Unauthorized request`:
  - validar header `X-API-Key`;
  - confirmar valor de `API_KEY` no ambiente.
- latência alta:
  - verificar `REDIS_URL`;
  - confirmar `CACHE_BACKEND=redis`;
  - checar `fallback_total` no `/api/metrics`.
- muitos fallbacks:
  - verificar saúde do banco e latência;
  - verificar se circuit breaker está abrindo com frequência.

---

## EN

### 1) Goal

This runbook explains how to deploy, validate and operate `Laborit Project` in production with baseline security, observability and quick troubleshooting.

### 2) Required variables

- `DB_USER`
- `DB_PASSWORD`
- `DB_HOST`
- `DB_PORT` (default `3306`)
- `DB_NAME`

Alternative: `DATABASE_URL` (takes precedence)

### 3) Recommended production variables

- `CACHE_BACKEND=redis`
- `REDIS_URL=<redis-url>`
- `CACHE_PREFIX=laborit`
- `API_KEY=<strong-secret>`

### 4) Runtime command (Render)

Build:

```bash
poetry install --no-interaction --no-ansi
```

Start:

```bash
poetry run uvicorn app.main:app --host 0.0.0.0 --port $PORT --workers 2
```

Health check path:

```text
/api/health
```

### 5) Post-deploy smoke tests

```bash
curl -s https://<service>.onrender.com/api/health
curl -s https://<service>.onrender.com/api/health/database
curl -s -H "X-API-Key: <API_KEY>" https://<service>.onrender.com/api/metrics
curl -s -X POST https://<service>.onrender.com/api/copilot/question \
  -H "Content-Type: application/json" \
  -H "X-API-Key: <API_KEY>" \
  -d '{"question":"How many customers do we have?"}'
```

### 6) Healthy operation signals

- `GET /api/health` returns `{"status":"ok"}`.
- `GET /api/health/database` returns `status: ok`.
- `/api/metrics` shows increasing `http.requests_total`.
- `fallback_total` stays relatively low.
- cache hit rate improves after warm-up.

### 7) Quick troubleshooting

- `Database connection failed`:
  - verify `DB_*`/`DATABASE_URL`;
  - verify network connectivity between app and DB.
- `Unauthorized request`:
  - verify `X-API-Key` header;
  - verify `API_KEY` env var value.
- high latency:
  - verify `REDIS_URL`;
  - verify `CACHE_BACKEND=redis`;
  - inspect `fallback_total` in `/api/metrics`.
- many fallbacks:
  - inspect DB health and latency;
  - check if circuit breaker opens frequently.
