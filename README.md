# Laborit Project

## 🇧🇷 Português (PT-BR)

### Visão geral

O `Laborit Project` é uma API em **FastAPI** para um **Copiloto Comercial**. A solução foi evoluída para atacar problemas reais de backend orientado a produto:

- tempo de resposta alto;
- fluxo excessivamente sequencial;
- baixa capacidade de escalar para múltiplas instâncias;
- pouca resiliência em falhas;
- necessidade de mais transparência e previsibilidade do fluxo.

Atualmente a arquitetura combina:

- **cache em dois níveis**;
- **cache distribuído com Redis**;
- **fallback automático para memória local** quando Redis não está disponível;
- **retry + timeout + circuit breaker**;
- **metadados por etapa** para transparência do fluxo;
- **arquitetura modular** para facilitar manutenção e evolução.

Dependências são gerenciadas com **Poetry** e o acesso a dados é feito via **SQLAlchemy**.

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
│       ├── cache.py
│       ├── circuit_breaker.py
│       └── database.py
├── tests/
└── README.md
```

---

### Endpoints disponíveis

- `GET /api/health`
- `GET /api/health/database`
- `GET /api/metrics`
- `POST /api/copilot/question`

#### Para que servem os endpoints de health?

- `GET /api/health`: confirma que a API está viva.
- `GET /api/health/database`: confirma que a API também consegue se conectar ao banco.

Eles **não fazem parte do fluxo de negócio** do copilot, mas são essenciais para deploy, monitoramento e troubleshooting.

#### Segurança de acesso (API key)

Se `API_KEY` estiver definida no ambiente, os endpoints abaixo exigem header `X-API-Key`:

- `POST /api/copilot/question`
- `GET /api/metrics`

Exemplo:

```bash
export API_KEY=super-secret
curl -H "X-API-Key: super-secret" http://localhost:8000/api/metrics
```

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

### Redis e escalabilidade real

Esta task adiciona **cache distribuído com Redis** para permitir escalabilidade horizontal real.

#### Por que Redis?

O cache anterior era apenas em memória local do processo. Isso funciona bem em ambiente simples, mas tem limitações:

- cada instância da API mantém seu próprio cache;
- dados não são compartilhados entre réplicas;
- hits de cache ficam inconsistentes em ambiente com múltiplos pods/containers;
- restart do processo apaga todo o estado local.

Com Redis:

- o cache é **compartilhado entre instâncias**;
- múltiplos nós da API usam o mesmo backend de cache;
- o sistema escala horizontalmente com comportamento previsível;
- o ganho de performance passa a existir no nível da aplicação inteira, não só do processo local.

#### Configuração de cache

Variáveis suportadas:

- `CACHE_BACKEND=in-memory|redis`
- `REDIS_URL=redis://localhost:6379/0`
- `CACHE_PREFIX=laborit`

Exemplo local com Redis:

```bash
export CACHE_BACKEND=redis
export REDIS_URL=redis://localhost:6379/0
export CACHE_PREFIX=laborit
poetry run uvicorn app.main:app --reload
```

Exemplo com Docker:

```bash
docker run --name laborit-redis -p 6379:6379 -d redis:7
export CACHE_BACKEND=redis
export REDIS_URL=redis://localhost:6379/0
poetry run uvicorn app.main:app --reload
```

#### Fallback seguro

Se `CACHE_BACKEND=redis` estiver configurado, mas Redis não estiver acessível, a aplicação faz fallback automático para:

- `backend_name = in-memory-fallback`

Isso evita indisponibilidade total da API por falha do cache distribuído.

### Observabilidade operacional

Além da `metadata` de cada resposta, a API agora expõe `GET /api/metrics` com visão agregada de execução:

- volume HTTP total;
- distribuição por endpoint e status code;
- latência média e máxima;
- total de requests do copilot;
- total de fallbacks;
- hits/misses de cache de resposta e dados.

### Concorrência prática (estado atual)

As rotas seguem `async` e o endpoint de pergunta executa o trecho síncrono pesado em threadpool (`run_in_threadpool`), reduzindo bloqueio do event loop e melhorando concorrência sob carga.

---

### Fluxo da requisição (detalhado)

1. A API recebe e valida a pergunta.
2. O `Orchestrator` cria o contexto da requisição (`trace_id`, timers, steps).
3. O `response_cache` é consultado primeiro.
	- Se houver hit, a resposta final volta imediatamente.
4. Em miss, `QueryService` interpreta a pergunta e gera um `QueryPlan`.
5. O `data_cache` é consultado usando a chave gerada por `QueryPlan.data_cache_key()`.
	- Se houver hit, o banco é poupado.
6. Em miss, `DataService` consulta o banco usando SQLAlchemy.
	- A execução passa por `run_with_resilience()`.
7. O resultado estruturado segue para o `LLMService`.
8. `LLMService` gera o texto final.
	- Também sob controle de retry/timeout/circuit breaker.
9. Se houver falha em dados ou geração, o fluxo produz fallback amigável.
10. O `ResponseBuilder` monta o payload final.
11. A resposta retorna junto com `metadata` contendo cache, breakers, steps e duração.

---

### Arquitetura e responsabilidades

#### `app/domain/query.py`

- `QueryIntent` (`Enum`): lista fechada dos intents suportados.
- `QueryPlan` (`dataclass`): contrato formal entre interpretação e execução.
- `data_cache_key()`: regra centralizada da chave do cache de dados.

#### `app/services/query_service.py`

- interpreta a linguagem natural do usuário;
- converte texto em `QueryPlan`;
- não acessa banco nem gera texto final.

#### `app/services/data_service.py`

- executa consultas SQLAlchemy com base no `QueryPlan`;
- retorna payload estruturado para a camada de resposta;
- não conhece HTTP, cache ou renderização textual.

#### `app/services/llm_service.py`

- transforma dados estruturados em linguagem natural;
- também fornece a estratégia de fallback textual.

#### `app/utils/cache.py`

- `CacheBackend`: contrato mínimo de cache;
- `InMemoryTTLCache`: backend local para desenvolvimento/fallback;
- `RedisTTLCache`: backend distribuído real para múltiplas instâncias;
- `create_cache_backend()`: factory que escolhe Redis ou memória a partir da configuração.

#### `app/orchestrator/resilience.py`

- `run_step()`: instrumentação por etapa;
- `run_with_resilience()`: retry + timeout + circuit breaker.

#### `app/orchestrator/metadata.py`

- `build_request_metadata()`: padroniza a metadata final;
- inclui status de cache, backends usados, circuit breakers, steps e duração.

#### `app/orchestrator/orchestrator.py`

- coordena o fluxo completo;
- decide entre cache, execução live e fallback;
- mantém o pipeline legível e de alto nível.

---

### Decisões arquiteturais (e por quê)

1. **Enum para intent (`QueryIntent`)**
	- elimina strings soltas espalhadas;
	- reduz bugs por typo;
	- torna o domínio mais explícito.

2. **`QueryPlan` como contrato formal**
	- separa interpretação da pergunta da execução técnica;
	- facilita testes unitários e manutenção.

3. **Resiliência extraída para módulo próprio**
	- evita poluir o `Orchestrator` com detalhe técnico;
	- deixa retry/timeout/circuit breaker reutilizáveis e testáveis.

4. **Metadata centralizada**
	- qualquer evolução do contrato observável fica em um único lugar;
	- garante consistência entre caminhos felizes e degradados.

5. **Redis como backend de cache distribuído**
	- resolve a limitação estrutural do cache em memória em ambiente com múltiplas instâncias;
	- é a base real de escalabilidade horizontal.

6. **Fallback para memória local quando Redis falha**
	- evita indisponibilidade total por dependência do cache;
	- mantém o sistema funcional mesmo com degradação parcial.

7. **Orchestrator como coordenador de fluxo**
	- melhora clareza do pipeline;
	- reduz acoplamento;
	- facilita onboarding e evolução futura.

---

### Contrato de resposta

`POST /api/copilot/question` retorna:

- `answer`: texto final para o usuário;
- `metadata.trace_id`: ID de correlação;
- `metadata.intent`: intent detectado;
- `metadata.cache.response_cache`: hit/miss;
- `metadata.cache.data_cache`: hit/miss;
- `metadata.cache.backend`: backend agregado (`redis`, `in-memory`, `in-memory-fallback`, `mixed`);
- `metadata.cache.response_backend`: backend do cache de resposta;
- `metadata.cache.data_backend`: backend do cache de dados;
- `metadata.explainability`: resumo do caminho de execução (`path`, `data_origin`, fallback e quantidade de etapas);
- `metadata.steps`: execução por etapa;
- `metadata.fallback_used`: indica resposta degradada;
- `metadata.total_duration_ms`: duração total da requisição.

---

### Como cada problema original foi atacado

#### 1) O tempo de resposta é alto

**Solução aplicada:**

- cache em dois níveis (`response_cache` e `data_cache`);
- hits de resposta evitam processamento completo;
- hits de dados evitam acesso repetido ao banco.

**Evolução com Redis:**

- agora o ganho de cache pode ser compartilhado entre instâncias, não apenas dentro de um processo.

#### 2) O processamento é majoritariamente sequencial

**Solução aplicada:**

- ainda existe um pipeline ordenado por natureza do domínio;
- porém o fluxo agora é controlado com timeout, retry e circuit breaker;
- o custo de repetição caiu fortemente por uso de cache.

#### 3) Há dificuldade em escalar o sistema conforme o volume cresce

**Solução aplicada:**

- cache distribuído com Redis;
- estado compartilhado entre instâncias;
- base pronta para múltiplos nós da API.

**Este é o principal problema resolvido por esta task.**

#### 4) Falta resiliência em cenários de falha

**Solução aplicada:**

- retry;
- timeout;
- circuit breaker;
- fallback amigável.

#### 5) Existem riscos relacionados à segurança

**Solução aplicada até agora:**

- uso de variáveis de ambiente para credenciais;
- mensagens seguras de erro de banco;
- proteção por `API_KEY` para endpoint de negócio e métricas;
- separação mais clara das responsabilidades.

**Próximos passos naturais:**

- autenticação/autorização;
- auditoria;
- mascaramento de dados sensíveis.

#### 6) A equipe de produto não tem visibilidade clara do dia a dia

**Solução aplicada:**

- metadata detalhada por requisição;
- status de cache;
- timings por etapa;
- estado dos circuit breakers.

#### 7) É difícil entender como as respostas são geradas

**Solução aplicada:**

- arquitetura modular;
- responsabilidades separadas;
- fluxo explícito no `Orchestrator`;
- documentação detalhada neste README.

#### 8) Não há transparência suficiente para análise e evolução do sistema

**Solução aplicada:**

- metadata estruturada;
- steps por execução;
- documentação de arquitetura;
- testes unitários e de fluxo com alta cobertura.

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
- mensagens de erro não devem vazar DSN, senha ou topologia sensível.

---

### Qualidade e testes

- testes unitários e de fluxo cobrem serviços, orquestração, cache, resiliência e endpoints;
- cobertura de referência nesta etapa: **31 testes passando**;
- cobertura total do pacote `app`: **99%**.

Comando oficial de cobertura:

```bash
poetry run pytest --cov=app --cov-report=term-missing -q
```

---

## 🇺🇸 English (EN)

### Overview

`Laborit Project` is a **FastAPI** API for a **Commercial Copilot**. The system was evolved to address real backend/product issues:

- high response time;
- mostly sequential processing;
- limited horizontal scalability;
- low resilience in failure scenarios;
- lack of transparency and operational clarity.

The current architecture combines:

- **two-level cache**;
- **distributed Redis cache**;
- **safe in-memory fallback** when Redis is unavailable;
- **retry + timeout + circuit breaker**;
- **per-step metadata** for observability;
- **modular architecture** for maintainability.

Dependencies are managed with **Poetry**, and persistence is handled via **SQLAlchemy**.

---

### Available endpoints

- `GET /api/health`
- `GET /api/health/database`
- `GET /api/metrics`
- `POST /api/copilot/question`

`/api/health` checks whether the API process is alive.

`/api/health/database` checks whether the API can also reach the database.

These endpoints are **operational endpoints**, not part of the business request pipeline.

#### Access security (API key)

If `API_KEY` is set, the endpoints below require header `X-API-Key`:

- `POST /api/copilot/question`
- `GET /api/metrics`

Example:

```bash
export API_KEY=super-secret
curl -H "X-API-Key: super-secret" http://localhost:8000/api/metrics
```

---

### Setup and run

```bash
poetry install
poetry run uvicorn app.main:app --reload
poetry run pytest -q
poetry run pytest --cov=app --cov-report=term-missing -q
```

#### Redis configuration

```bash
export CACHE_BACKEND=redis
export REDIS_URL=redis://localhost:6379/0
export CACHE_PREFIX=laborit
poetry run uvicorn app.main:app --reload
```

Optional local Redis with Docker:

```bash
docker run --name laborit-redis -p 6379:6379 -d redis:7
```

### Operational observability

Beyond per-request `metadata`, the API now exposes `GET /api/metrics` with aggregated runtime visibility:

- total HTTP volume;
- per-endpoint and per-status distribution;
- average and max latency;
- total copilot requests;
- total fallbacks;
- response/data cache hit-miss counters.

### Practical concurrency (current state)

Routes remain `async`, and the heavy sync execution path in the question endpoint now runs through threadpool (`run_in_threadpool`), reducing event-loop blocking and improving concurrency under load.

---

### Request flow

1. API validates input.
2. `Orchestrator` initializes request context.
3. `response_cache` is checked first.
4. On miss, `QueryService` builds a `QueryPlan`.
5. `data_cache` is checked using `QueryPlan.data_cache_key()`.
6. On miss, `DataService` fetches data through resilient execution.
7. `LLMService` generates the final answer.
8. If data/LLM fails, fallback text is produced.
9. `ResponseBuilder` returns `message + metadata`.

---

### Architecture modules

- `app/domain/query.py`: domain intent enum + formal query contract.
- `app/services/query_service.py`: transforms user language into `QueryPlan`.
- `app/services/data_service.py`: resolves `QueryPlan` into structured data.
- `app/services/llm_service.py`: generates final text and fallback text.
- `app/utils/cache.py`: in-memory cache, Redis cache, cache factory and fallback behavior.
- `app/orchestrator/resilience.py`: retry/timeout/circuit-breaker engine.
- `app/orchestrator/metadata.py`: unified response metadata builder.
- `app/orchestrator/orchestrator.py`: high-level coordinator of the full pipeline.

---

### Architecture decisions (why)

1. **Intent enum (`QueryIntent`)**
	- removes typo-prone raw strings;
	- improves readability and type safety.

2. **Formal `QueryPlan` contract**
	- clear boundary between interpretation and execution;
	- easier isolated tests.

3. **Dedicated resilience module**
	- keeps orchestration logic clean;
	- centralizes retry/timeout/circuit-breaker behavior.

4. **Dedicated metadata builder**
	- one place for observable response schema changes;
	- ensures consistency across all execution paths.

5. **Redis as distributed cache backend**
	- solves the core limitation of process-local cache;
	- enables real horizontal scalability.

6. **Safe fallback to in-memory cache**
	- prevents total API failure if Redis is temporarily unavailable.

7. **Orchestrator as flow coordinator**
	- lower coupling;
	- easier maintenance;
	- clearer end-to-end pipeline.

---

### Response contract

`POST /api/copilot/question` returns:

- `answer`
- `metadata.trace_id`
- `metadata.intent`
- `metadata.cache.response_cache`
- `metadata.cache.data_cache`
- `metadata.cache.backend`
- `metadata.cache.response_backend`
- `metadata.cache.data_backend`
- `metadata.explainability`
- `metadata.steps`
- `metadata.fallback_used`
- `metadata.total_duration_ms`

---

### How each original problem was addressed

#### 1) High response time

**Solution:** two-level cache (`response_cache` + `data_cache`) and cross-instance reuse through Redis.

#### 2) Mostly sequential processing

**Solution:** the business pipeline remains ordered, but is now controlled by timeout/retry/circuit breaker and heavily optimized through cache reuse.

#### 3) Difficulty scaling with traffic growth

**Solution:** distributed Redis cache and shared state across API instances.

**This is the main problem addressed by this task.**

#### 4) Lack of resilience

**Solution:** retry, timeout, circuit breaker and friendly fallback.

#### 5) Security risks in data access

**Current solution:** env-based credentials, safe DB error messages, API key protection for business/metrics endpoints, clearer boundaries between layers.

**Future work:** auth, auditing and sensitive-data masking.

#### 6) Product team lacks visibility

**Solution:** structured metadata, cache status, step timings and breaker state.

#### 7) Hard to understand how answers are generated

**Solution:** modular architecture, explicit orchestration flow and detailed documentation.

#### 8) Low transparency for analysis and evolution

**Solution:** response metadata, execution steps, architecture documentation and high automated test coverage.

---

### Database

- MySQL via `mysql+pymysql`
- Target DB: `northwind`
- Mapped tables: `customers`, `employees`, `orders`, `products`

Configuration priority:

1. `DATABASE_URL`
2. `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT`, `DB_NAME`

Security notes:

- never hardcode credentials;
- use environment variables;
- do not leak DSN/password in error responses.

---

### Quality and tests

- unit and flow tests cover services, orchestration, cache, resilience and endpoints;
- reference status for this task: **31 tests passing**;
- total `app` package coverage: **99%**.
