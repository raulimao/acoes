# 📊 Fundamentus Dashboard

![Python](https://img.shields.io/badge/Python-3.8%2B-blue?logo=python)
![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)
![Streamlit](https://img.shields.io/badge/Streamlit-Cloud-orange?logo=streamlit)
![Supabase](https://img.shields.io/badge/Supabase-Database-3ECF8E?logo=supabase)

Dashboard para análise de ações da B3 com base em indicadores fundamentalistas do [Fundamentus](https://www.fundamentus.com.br/).

## 🔍 Funcionalidades

- ✅ Coleta automática de dados do Fundamentus
- ✅ **4 estratégias de investimento**: Graham, Greenblatt, Bazin, Qualidade
- ✅ **Super Score** combinando todas as estratégias com pesos
- ✅ Filtros por **Setor/Subsetor**
- ✅ **Histórico** de ações qualificadas (Supabase)
- ✅ Chat AI (Groq) para consultas sobre ações
- ✅ Comparação de ativos com gráfico radar

## 🏗️ Estrutura do Projeto

```
acoes/
├── app/                    # Interface Streamlit
│   └── main.py             # Aplicação principal
├── core/                   # Lógica de negócio
│   ├── fundamentus/        # Scraper e cleaner
│   ├── scoring/            # Sistema de pontuação
│   └── pipeline.py         # Pipeline de dados
├── services/               # Serviços externos
│   ├── ai_chat.py          # Chat Groq AI
│   ├── auth_service.py     # Autenticação
│   ├── history_service.py  # Histórico (Supabase)
│   └── supabase_client.py  # Cliente Supabase
├── config/                 # Configurações
│   ├── settings.py         # Constantes
│   └── strategies_config.py # Estratégias e filtros
├── .env                    # Variáveis de ambiente
├── config.yaml             # Config autenticação
└── requirements.txt        # Dependências
```

## 🚀 Como usar

### 1. Clone o repositório
```bash
git clone https://github.com/raulimao/acoes.git
cd acoes
```

### 2. Crie e ative o ambiente virtual
```bash
python -m venv venv
.\venv\Scripts\activate  # Windows
source venv/bin/activate  # Linux/Mac
```

### 3. Instale as dependências
```bash
pip install -r requirements.txt
```

### 4. Configure as variáveis de ambiente
Crie um arquivo `.env` com:
```env
GROQ_API_KEY="sua_chave_groq"
SUPABASE_URL="https://seu-projeto.supabase.co"
SUPABASE_KEY="sua_chave_supabase"
```

### 5. Execute o dashboard
```bash
streamlit run app/main.py
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