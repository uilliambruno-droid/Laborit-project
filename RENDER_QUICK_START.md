# 🚀 Quick Start - Deploy no Render (Plano FREE)

## ⚡ Resumo Rápido

```
[GitHub main branch] → [Render FREE] → [MySQL] → ✅ Production (Sem Redis!)
```

---

## 1️⃣ Preparar Banco de Dados (2 min)

### ✅ Opção Recomendada: PlanetScale (MySQL Cloud)

1. https://planetscale.com → Sign up (grátis)
2. Criar database: `laborit-db`
3. Ir para **"Connections"** → Gerar **"Password"**
4. Copiar connection string MySQL (formato: `mysql://user:pass@pscale_host:3306/laborit-db`)

### ✅ Alternativa: Render MySQL (Grátis também)

1. https://render.com/dashboard
2. "New +" → "MySQL"
3. Nome: `laborit-mysql`
4. Copiar connection string

### ⚠️ NÃO precisa de Redis!

O sistema **já suporta cache em memória** (fallback automático). Redis era uma otimização opcional, não obrigatória.

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
| **Plan** | ⭐ `Free` (não standard!) |
| **Region** | `São Paulo` |
| **Auto-deploy** | ✅ ON |

### Passo 4: Adicionar Variáveis de Ambiente (SIMPLES!)

Clique em **"Environment"** e adicione APENAS:

```env
DATABASE_URL=mysql://user:pass@pscale_host:3306/laborit-db
ENVIRONMENT=production
LOG_LEVEL=INFO
CACHE_BACKEND=inmemory
API_KEY=<gerar com: openssl rand -hex 32>
```

**Pronto! Sem Redis!**

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

## 5️⃣ Acessar Banco Direto (MySQL Workbench, DBeaver, etc)

### 🔓 Sim! Você consegue acessar direto

Use a mesma **DATABASE_URL**:

```
mysql://user:pass@pscale_host:3306/laborit-db
```

### Exemplo com MySQL CLI:

```bash
# Se usar PlanetScale
mysql -u user -p -h pscale_host -P 3306 -D laborit-db

# Enter password quando pedido
# SELECT * FROM customers LIMIT 5;
```

### Exemplo com GUI:

1. **MySQL Workbench**: File → New Connection
   - Host: `pscale_host`
   - Port: `3306`
   - Username: `user`
   - Password: `pass`
   - Database: `laborit-db`

2. **DBeaver**: New Database Connection
   - Database: MySQL
   - Server Host: `pscale_host`
   - Port: 3306
   - User: `user`
   - Password: `pass`
   - Database: `laborit-db`

---

## 6️⃣ Troubleshooting Rápido

### ❌ Build fails
**Solução:** Render precisa instalar poetry. Já configurado em `render.yaml`.

### ❌ "502 Bad Gateway"
**Verificar:**
```bash
# Logs no Render Dashboard → "Logs" tab
# Procure por: DATABASE_URL errors
```

### ❌ Database connection error
```bash
# Testar conexão local
mysql -u user -p -h host

# Ou com Python:
python -c "from sqlalchemy import create_engine; e = create_engine('DATABASE_URL'); print(e.connect())"
```

### ❌ "Plano Free foi suspenso"
- Render suspend apps free inativos por 15 minutos
- Acesse https://seu-app.onrender.com para reativar
- Ou faça um novo deploy (git push)

---

## 📋 Checklist Final

- ✅ PlanetScale ou Render MySQL criado
- ✅ DATABASE_URL copiada
- ✅ `main` branch no GitHub atualizado
- ✅ Serviço criado no Render (plano FREE)
- ✅ CACHE_BACKEND=inmemory (sem Redis!)
- ✅ API_KEY gerada
- ✅ Health check retorna `healthy`
- ✅ Testes com API Key funcionam
- ✅ Acessar banco direto via MySQL Workbench/CLI

---

## 🔗 URLs Importantes

| Recurso | Link |
|---------|------|
| **Dashboard Render** | https://render.com/dashboard |
| **Seu App** | https://seu-app-name.onrender.com |
| **Seu App (Health)** | https://seu-app-name.onrender.com/api/health |
| **Seu App (Docs)** | https://seu-app-name.onrender.com/docs |
| **Logs** | Dashboard → Seu serviço → "Logs" |
| **GitHub Repo** | https://github.com/uilliambruno-droid/Laborit-project |
| **PlanetScale** | https://planetscale.com |

---

## 💡 Por Que Sem Redis?

1. **Cache em memória é suficiente** para começar
2. **Redis = custo extra** (cloud) ou complexidade (self-hosted)
3. **Sistema já tem fallback automático** para in-memory
4. **Plano FREE do Render** tem limite de recursos
5. **Pode adicionar Redis depois** se precisar escalar

Se precisar adicionar Redis depois:
```env
CACHE_BACKEND=redis
REDIS_URL=redis://:password@host:port
```

Mas por agora: **CACHE_BACKEND=inmemory** é perfeito! ✅

---

## 🆘 Suporte Rápido

| Problema | Comando/Solução |
|----------|---------|
| Ver logs | `Render Dashboard → Logs` |
| Forçar redeploy | `Render Dashboard → "Redeploy"` |
| Testar BD local | `mysql -u user -p -h host` |
| Gerar API Key | `openssl rand -hex 32` |
| App suspenso (FREE) | Acesse URL para reativar |

---

**Pronto! 🎉 API deve estar live em ~10 minutos SEM Redis!**
