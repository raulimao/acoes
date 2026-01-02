# 📊 NorteAcoes - Dashboard de Ações

![Python](https://img.shields.io/badge/Python-3.11%2B-blue?logo=python)
![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)
![Next.js](https://img.shields.io/badge/Next.js-16-black?logo=next.js)
![FastAPI](https://img.shields.io/badge/FastAPI-0.109-009688?logo=fastapi)
![Supabase](https://img.shields.io/badge/Supabase-Database-3ECF8E?logo=supabase)

Dashboard para análise de ações da B3 com base em indicadores fundamentalistas do [Fundamentus](https://www.fundamentus.com.br/).

## 🔍 Funcionalidades

- ✅ Coleta automática de dados do Fundamentus
- ✅ **4 estratégias de investimento**: Graham, Greenblatt, Bazin, Qualidade
- ✅ **Super Score** combinando todas as estratégias com pesos
- ✅ Filtros por **Setor/Subsetor**
- ✅ **Histórico** de ações qualificadas (Supabase)
- ✅ Chat AI (Groq) para consultas sobre ações
- ✅ Sistema de **Premium** com Stripe
- ✅ Autenticação com Supabase Auth

## 🏗️ Estrutura do Projeto

```
acoes/
├── api/                    # Backend FastAPI
│   ├── main.py             # API principal
│   └── services/           # Serviços (auth, payment, etc)
├── frontend/               # Frontend Next.js
│   └── src/                # Código fonte React
├── core/                   # Lógica de negócio
│   ├── fundamentus/        # Scraper e cleaner
│   ├── scoring/            # Sistema de pontuação
│   └── pipeline.py         # Pipeline de dados
├── config/                 # Configurações
│   ├── settings.py         # Constantes
│   └── strategies_config.py # Estratégias e filtros
├── scripts/                # Scripts de manutenção
│   ├── refresh_data.py     # Atualizar dados manualmente
│   └── seed_config.py      # Popular config no Supabase
├── .env                    # Variáveis de ambiente
└── requirements.txt        # Dependências Python
```

## 🚀 Como usar

### 1. Clone o repositório
```bash
git clone https://github.com/raulimao/acoes.git
cd acoes
```

### 2. Backend (API FastAPI)
```bash
python -m venv venv
.\venv\Scripts\activate  # Windows
source venv/bin/activate  # Linux/Mac

pip install -r requirements.txt
uvicorn api.main:app --reload
```
A API roda em `http://localhost:8000`

### 3. Frontend (Next.js)
```bash
cd frontend
npm install
npm run dev
```
O frontend roda em `http://localhost:3000`

### 4. Configure as variáveis de ambiente
Crie um arquivo `.env` com:
```env
# Supabase
SUPABASE_URL="https://seu-projeto.supabase.co"
SUPABASE_KEY="sua_chave_supabase"
SUPABASE_SERVICE_KEY="sua_service_key"

# AI
GROQ_API_KEY="sua_chave_groq"

# Pagamentos
STRIPE_SECRET_KEY="sk_..."
STRIPE_WEBHOOK_SECRET="whsec_..."

# JWT
JWT_SECRET_KEY="sua_chave_secreta"
```

## 📈 Estratégias de Investimento

| Estratégia | Peso | Filtros |
|------------|------|---------|
| Graham | 1.0x | P/L, P/VP, Liquidez, Dívida |
| Greenblatt | 1.5x | ROIC, EV/EBIT |
| Bazin | 1.0x | DY, Dívida, P/L |
| Qualidade | 2.0x | ROE, Margem, ROIC, Dívida |

## 📄 Licença

MIT License - [@raulimao](https://github.com/raulimao)