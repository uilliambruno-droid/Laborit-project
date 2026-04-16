# 🚀 Guia de Deploy no Render

## Pré-requisitos

1. **Conta Render**: https://render.com (gratuita ou paga)
2. **Repositório Git**: GitHub com branch `main` atualizado
3. **Banco de dados MySQL**: (pode usar Render ou cloud externo como PlanetScale, Amazon RDS)
4. **Redis**: (pode usar Render ou Redis Cloud)
5. **Git configurado localmente**

---

## 1️⃣ Preparação do Repositório

### Garantir que tudo está no GitHub

```bash
cd /Users/uilliamsantos/Documents/Laborit-Project

# Verificar branch e commits
git branch -vv
git log --oneline -5

# Garantir que tudo está sincronizado
git push origin main
```

**Esperado:**
- Branch `main` atualizado
- Todos os commits enviados para origin
- `render.yaml` presente na raiz

### Verificar arquivo render.yaml

```bash
ls -la render.yaml
cat render.yaml
```

---

## 2️⃣ Preparar Banco de Dados MySQL

### Opção A: Render MySQL (Simples, recomendado para teste)

1. Acesse https://render.com/dashboard
2. Clique em **"New +"** → **"MySQL"**
3. Preencha:
   - **Name**: `laborit-mysql`
   - **Database**: `laborit_db`
   - **Username**: `laborit_user`
   - **Region**: Mesma região da API (ex: São Paulo)
4. Clique **"Create Database"**
5. Aguarde 3-5 minutos
6. **Copie a connection string** (formato: `mysql://user:pass@host:3306/db`)

### Opção B: PlanetScale (MySQL Cloud, melhor para produção)

1. Acesse https://planetscale.com
2. Crie uma nova database: `laborit-db`
3. Vá para **"Connections"** → Gere **"Password"**
4. Copie a connection string MySQL

### Opção C: Amazon RDS MySQL

1. Crie instância RDS com MySQL
2. Configure security groups (porta 3306 acessível)
3. Copie endpoint

---

## 3️⃣ Preparar Redis

### Opção A: Render Redis (Simples)

1. Acesse https://render.com/dashboard
2. Clique em **"New +"** → **"Redis"**
3. Preencha:
   - **Name**: `laborit-redis`
   - **Region**: Mesma região da API
4. Clique **"Create"**
5. Aguarde 2-3 minutos
6. **Copie a connection string** (formato: `redis://:password@host:port`)

### Opção B: Redis Cloud (Popular, gratuito até certo limite)

1. Acesse https://redis.com/cloud/
2. Crie database gratuita
3. Copie connection string

---

## 4️⃣ Criar a API Web Service no Render

### Passo 1: Conectar GitHub

1. Acesse https://render.com/dashboard
2. Clique em **"New +"** → **"Web Service"**
3. Selecione **"Connect repository"**
4. Autorize Render com sua conta GitHub
5. Selecione repositório **`Laborit-project`**
6. Clique **"Connect"**

### Passo 2: Configurar Serviço

**Preencha os campos:**

| Campo | Valor |
|-------|-------|
| **Name** | `laborit-copilot-api` |
| **Environment** | `Python 3` |
| **Build Command** | `pip install poetry && poetry install --no-root && poetry install` |
| **Start Command** | `poetry run uvicorn app.main:app --host 0.0.0.0 --port $PORT` |
| **Branch** | `main` |
| **Auto-deploy** | ✅ Ativado |
| **Plan** | `Standard` ($7/mês) ou `Pro` ($12/mês) |
| **Region** | `São Paulo (Brazil South)` |

### Passo 3: Adicionar Variáveis de Ambiente

Clique em **"Environment"** e adicione:

```env
# Obrigatórias
DATABASE_URL=mysql://user:password@host:3306/laborit_db
REDIS_URL=redis://:password@host:port

# Recomendadas
ENVIRONMENT=production
LOG_LEVEL=INFO
CACHE_BACKEND=redis
API_KEY=seu_api_key_secreto_aqui

# Timeouts (em ms)
QUERY_TIMEOUT_MS=10000
DATA_TIMEOUT_MS=15000
LLM_TIMEOUT_MS=30000

# Cache TTL (em segundos)
RESPONSE_CACHE_TTL=3600
DATA_CACHE_TTL=1800
```

### Passo 4: Criar Instância

Clique em **"Create Web Service"** e aguarde o build (5-10 minutos)

---

## 5️⃣ Testes Após Deploy

### Verificar Logs

Na dashboard Render:
1. Selecione seu serviço
2. Clique em **"Logs"** (lado direito)
3. Procure por erros

### Testar Health Check

```bash
# Substitua YOUR_RENDER_URL pela URL fornecida
curl -X GET https://your-app-name.onrender.com/api/health

# Esperado:
# {"status": "healthy", "timestamp": "2026-04-16T..."}
```

### Testar Endpoint Copilot (sem API Key)

```bash
curl -X POST https://your-app-name.onrender.com/api/copilot/question \
  -H "Content-Type: application/json" \
  -d '{"user_input": "Oi, tudo bem?"}'

# Se API_KEY está configurada, receberá:
# {"detail": "Missing API Key"}

# Teste COM chave:
curl -X POST https://your-app-name.onrender.com/api/copilot/question \
  -H "Content-Type: application/json" \
  -H "X-API-Key: seu_api_key_secreto_aqui" \
  -d '{"user_input": "Quantos clientes ativos?"}'
```

### Verificar Métricas

```bash
# Com API Key configurada:
curl -X GET https://your-app-name.onrender.com/api/metrics \
  -H "X-API-Key: seu_api_key_secreto_aqui"

# Esperado:
# {
#   "http_requests_total": 5,
#   "copilot_requests_total": 2,
#   "cache_hits": 1,
#   "cache_misses": 1,
#   ...
# }
```

---

## 6️⃣ Troubleshooting

### ❌ Build falha com "poetry not found"

**Solução:** Render precisa instalar poetry primeiro

```yaml
buildCommand: pip install poetry && poetry install
```

### ❌ Database connection error

**Verificar:**
1. `DATABASE_URL` está correto?
2. Firewall permite conexão de Render?
3. Credenciais corretas (user:pass)?

```bash
# Testar conexão localmente
poetry run python -c "from sqlalchemy import create_engine; e = create_engine('DATABASE_URL'); print('OK')"
```

### ❌ Redis connection error

**Verificar:**
1. `REDIS_URL` está no formato correto?
2. `CACHE_BACKEND=redis` configurado?
3. Fallback para `inmemory` disponível?

### ❌ Timeout na requisição

**Verificar:**
1. Os timeouts estão muito curtos?
2. Database/Redis respondendo lentamente?
3. Aumentar `QUERY_TIMEOUT_MS`, `DATA_TIMEOUT_MS`, `LLM_TIMEOUT_MS`

### ❌ "Port already in use"

**Solução:** Render define `$PORT` automaticamente. Usar:
```bash
poetry run uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

---

## 7️⃣ Monitoramento em Produção

### Verificar Status Regularmente

```bash
# Logs em tempo real
curl -X GET "https://your-app-name.onrender.com/api/health" \
  -w "\nStatus: %{http_code}\n"

# Métricas de performance
curl -X GET "https://your-app-name.onrender.com/api/metrics" \
  -H "X-API-Key: seu_api_key_secreto_aqui" | jq .
```

### Alertas Recomendados

Ativar em Render Dashboard:
- ✅ **Notificações de erro** (>5 500 errors em 5 min)
- ✅ **CPU > 80%** por 5 minutos
- ✅ **Memória > 85%** por 5 minutos
- ✅ **Build falha**

### Logs Estruturados

Verifique regularmente:
```bash
# Ver últimas 100 linhas
curl -X GET https://your-app-name.onrender.com/api/health | jq .
```

---

## 8️⃣ Atualizar em Produção

### Deploy Automático (recomendado)

1. Faça commit e push para `main`
```bash
git add .
git commit -m "chore: update configuration"
git push origin main
```

2. Render detecta automaticamente e inicia novo build
3. Monitorar em **Render Dashboard** → **Deployments**

### Deploy Manual

Se precisar redeploiar manualmente:
1. Acesse Render Dashboard
2. Selecione seu serviço
3. Clique **"Redeploy"** (lado direito)

---

## 9️⃣ Segurança em Produção

### Checklist de Segurança

- ✅ `API_KEY` configurado com valor forte (32+ caracteres)
- ✅ `DATABASE_URL` não committed no git
- ✅ `REDIS_URL` não committed no git
- ✅ Firewall/Security Groups apenas permitem porta 3306 de Render
- ✅ SSL/HTTPS ativado automaticamente no Render
- ✅ `LOG_LEVEL=INFO` (não DEBUG em produção)
- ✅ Backups automáticos do banco configurados

### Gerar API Key Forte

```bash
# macOS/Linux
openssl rand -hex 32

# Resultado exemplo:
# a7f3c8d2e9b4f1a6c5e0d3f8a2b9c4e7f0a1d2c3e4f5a6b7c8d9e0f1a2b3c
```

---

## 🔟 Próximos Passos

1. ✅ Commit `render.yaml` no git
2. ✅ Criar serviços (MySQL + Redis) no Render
3. ✅ Criar Web Service com variáveis de ambiente
4. ✅ Aguardar build completar
5. ✅ Testar endpoints
6. ✅ Monitorar logs
7. ✅ Ativar alertas
8. ✅ Configurar backups

---

## 📞 Suporte

- **Render Docs**: https://render.com/docs
- **FastAPI Docs**: https://fastapi.tiangolo.com
- **SQLAlchemy Docs**: https://docs.sqlalchemy.org
- **Poetry Docs**: https://python-poetry.org/docs

---

**Última atualização**: 16 de Abril de 2026
