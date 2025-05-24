# 📊 Fundamentus Dashboard

![Python](https://img.shields.io/badge/Python-3.8%2B-blue?logo=python)
![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)
![Streamlit](https://img.shields.io/badge/Streamlit-Cloud-orange?logo=streamlit)

Este projeto automatiza a análise de ações listadas na B3 com base em indicadores fundamentalistas coletados diretamente do site [Fundamentus](https://www.fundamentus.com.br/). A análise é visualizada por meio de um dashboard interativo construído com **Streamlit** e **Plotly**.

## 🔍 Funcionalidades

- Coleta automática dos dados fundamentalistas de todas as ações da B3
- Padronização e limpeza dos dados (corrige formatações e inconsistências)
- Cálculo de score com base em 16 indicadores clássicos de Value Investing
- Visualização interativa dos dados filtrados e classificados
- Exportação de CSV com os resultados filtrados
- Comparação de múltiplas ações com gráfico de radar
- Interface interativa com filtros por Score, ordenação e seleção de indicadores

## 🚀 Como usar

### 1. Clone o repositório
```bash
git clone https://github.com/raulimao/acoes.git
cd acoes
```

### 2. Instale as dependências
```bash
pip install -r requirements.txt
```

### 3. Execute o script de coleta e cálculo
```bash
python processar_fundamentus.py
```

Isso irá gerar o arquivo `fundamentus_ranking_corrigido.csv` com os dados tratados e ranqueados.

### 4. Rode o dashboard
```bash
streamlit run streamlit_app.py
```

Ou acesse diretamente pelo Streamlit Cloud:
👉 [Acessar o Dashboard](https://h9aj34hulirujnukbubacg.streamlit.app)

## 📸 Demonstração

![demo](https://github.com/raulimao/acoes/assets/demo-screenshot.png)

## 📈 Score dos Ativos

O score de cada ativo é calculado com base na proximidade a critérios considerados ideais para investimentos de longo prazo:

| Indicador                | Regra Ideal |
|--------------------------|-------------|
| P/L                     | < 15        |
| P/VP                    | <= 1.5      |
| PSR                     | <= 1.5      |
| Dividend Yield          | > 4         |
| P/Ativo                 | <= 1.5      |
| P/Cap. Giro             | >= 1        |
| P/EBIT                  | < 12        |
| P/Ativ Circ. Líq.       | < 1.5       |
| EV/EBIT                 | < 10        |
| EV/EBITDA               | < 8         |
| Margem EBIT             | >= 10       |
| Margem Líquida          | >= 5        |
| Liquidez Corrente       | >= 1.5      |
| ROIC                    | > 10        |
| ROE                     | > 15        |
| Dívida Bruta / Patrim.  | < 0.5       |

O score é uma média ponderada da aderência a esses critérios.

## 📦 Estrutura do projeto

```bash
.
├── acoes.ipynb                      # Notebook exploratório (opcional)
├── processar_fundamentus.py        # Script de coleta e tratamento de dados
├── streamlit_app.py                # Aplicação Streamlit
├── fundamentus_ranking_corrigido.csv  # Resultado gerado
├── requirements.txt                # Dependências
└── README.md                       # Este arquivo
```

## 🧠 Pré-requisitos

- Python 3.8 ou superior
- Conexão com a internet (para acessar o Fundamentus)

## 📬 Contribuição

Pull requests são bem-vindos! Fique à vontade para sugerir melhorias, novos indicadores ou visualizações adicionais.

## ❓ FAQ

**Os dados são atualizados automaticamente?**
> Não. Para atualizar, execute novamente o script `processar_fundamentus.py`.

**Posso adicionar outros indicadores?**
> Sim! Adicione no dicionário `criterios` e ajuste o código conforme necessário.

## 📄 Licença

Distribuído sob a licença MIT. Veja `LICENSE` para mais informações.

---

Feito com 💻 por [@raulimao](https://github.com/raulimao) e [@felps2003](https://github.com/felps2003)  

