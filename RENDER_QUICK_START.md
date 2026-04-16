# 🚀 Quick Start - Deploy no Render em 10 Minutos

## ⚡ Resumo Rápido

```
[GitHub main branch] → [Render] → [MySQL + Redis] → ✅ Production
```

---

## 1️⃣ Preparar Credenciais (2 min)

### Banco de Dados MySQL

**Opção rápida (recomendado):** PlanetScale (MySQL cloud)

1. https://planetscale.com → Sign up
2. Criar database: `laborit-db`
3. Gerar connection string MySQL
4. Copie: `mysql://user:pass@pscale_host:3306/laborit-db`

### Redis

**Opção rápida:** Redis Cloud

1. https://redis.com/cloud → Sign up
2. Criar database (Free tier)
3. Copie: `redis://:password@host:port`

---

## 2️⃣ Criar Serviço no Render (3 min)

### Passo 1: Acessar Render
- https://render.com
- Login com GitHub
- Clique **"New +"** → **"Web Service"**

### Passo 2: Conectar Repositório
- Selecione **"Connect repository"**
- Escolha **`Laborit-project`**
- Branch: **`main`**
- Clique **"Connect"**

### Passo 3: Configurar Serviço

| Campo | Valor |
|-------|-------|
| **Name** | `laborit-copilot-api` |
| **Environment** | `Python 3` |
| **Build Cmd** | *(deixe o padrão)* |
| **Start Cmd** | *(deixe o padrão)* |
| **Plan** | `Standard ($7/mês)` |
| **Region** | `São Paulo` |
| **Auto-deploy** | ✅ ON |

### Passo 4: Adicionar Variáveis de Ambiente

Clique em **"Environment"** e adicione:

```env
DATABASE_URL=mysql://user:pass@pscale_host:3306/laborit-db
REDIS_URL=redis://:password@host:port
API_KEY=<gerar com: openssl rand -hex 32>
ENVIRONMENT=production
LOG_LEVEL=INFO
CACHE_BACKEND=redis
QUERY_TIMEOUT_MS=10000
DATA_TIMEOUT_MS=15000
LLM_TIMEOUT_MS=30000
```

### Passo 5: Criar
- Clique **"Create Web Service"**
- Aguarde build (5-10 min)
- Copie a URL gerada (ex: `https://laborit-copilot-api.onrender.com`)

---

## 3️⃣ Testar Deploy (2 min)

```bash
# Health check
curl https://seu-app.onrender.com/api/health

# Esperado:
# {"status": "healthy", "timestamp": "2026-04-16T..."}
```

✅ Se retornar `healthy`, está pronto!

---

## 4️⃣ Testar com API Key (1 min)

```bash
# Substitua YOUR_API_KEY pelo valor configurado
API_KEY="<seu api key>"
URL="https://seu-app.onrender.com"

# Teste 1: Métricas
curl -X GET "$URL/api/metrics" \
  -H "X-API-Key: $API_KEY"

# Teste 2: Pergunta simples
curl -X POST "$URL/api/copilot/question" \
  -H "X-API-Key: $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"user_input": "Oi, tudo bem?"}'

# Teste 3: Pergunta com dados
curl -X POST "$URL/api/copilot/question" \
  -H "X-API-Key: $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"user_input": "Quantos clientes ativos?"}'
```

---

## 5️⃣ Troubleshooting Rápido

### ❌ Build fails
**Solução:** Render precisa instalar poetry. Já configurado em `render.yaml`.

### ❌ "502 Bad Gateway"
**Verificar:**
```bash
# Logs no Render Dashboard → "Logs" tab
# Procure por: DATABASE_URL, REDIS_URL errors
```

### ❌ Database connection error
```bash
# Testar conexão local
python -c "from sqlalchemy import create_engine; e = create_engine('DATABASE_URL'); print(e.connect())"
```

### ❌ Timeout (jiahsdjdfhakfdhj error)
**Solução:** O sistema já previne isso com guidance flow. Tente aumentar timeouts:
```
QUERY_TIMEOUT_MS=15000
DATA_TIMEOUT_MS=20000
LLM_TIMEOUT_MS=40000
```

---

## 📋 Checklist Final

- ✅ `main` branch no GitHub atualizado
- ✅ `render.yaml` presente
- ✅ Serviço criado no Render
- ✅ Variáveis de ambiente configuradas
- ✅ Health check retorna `healthy`
- ✅ Testes com API Key funcionam
- ✅ Logs monitorados

---

## 🔗 URLs Importantes

| Recurso | Link |
|---------|------|
| **Dashboard Render** | https://render.com/dashboard |
| **Seu App** | https://seu-app.onrender.com |
| **Seu App (Health)** | https://seu-app.onrender.com/api/health |
| **Seu App (Docs)** | https://seu-app.onrender.com/docs |
| **Logs** | Dashboard → Seu serviço → "Logs" |
| **GitHub Repo** | https://github.com/uilliambruno-droid/Laborit-project |

---

## 💡 Dicas Importantes

1. **Auto-deploy**: Qualquer push para `main` redeploy automaticamente
2. **Health check**: `/api/health` chamado a cada 30 segundos
3. **Fallback**: Redis fora? Sistema cai para in-memory cache
4. **Logs**: Acessar via Dashboard Render em tempo real
5. **Alertas**: Ativar notificações de erro no Render Dashboard

---

## 🆘 Suporte Rápido

| Problema | Comando |
|----------|---------|
| Ver logs | `Render Dashboard → Logs` |
| Forçar redeploy | `Render Dashboard → "Redeploy"` |
| Reiniciar app | `Render Dashboard → "Restart"` |
| Testar BD local | `poetry run python` → `from sqlalchemy import create_engine` |
| Testar Redis local | `redis-cli ping` |

---

**Pronto! 🎉 API deve estar live em ~10 minutos.**

Para troubleshooting avançado, veja: [`RENDER_DEPLOY_GUIDE.md`](RENDER_DEPLOY_GUIDE.md)
