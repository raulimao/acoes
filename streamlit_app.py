import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from processar_fundamentus import resultado
from src.chat import mensagem_cli

# --- Config
st.set_page_config(page_title="Dashboard Fundamentus", layout="wide")

# --- Dados
@st.cache_data
def carregar_dados():
    return resultado()

df = carregar_dados()

# --- Sidebar
st.sidebar.header("🔎 Filtros")
min_score = st.sidebar.slider("Score mínimo", 0, 100, 60)
coluna_ordenacao = st.sidebar.selectbox("Ordenar por", df.columns[df.dtypes != 'object'], index=0)
top_n = st.sidebar.slider("Top N", 5, 50, 10)

df_filtrado = df[df["score"] >= min_score].sort_values(by=coluna_ordenacao, ascending=False)

# --- Layout principal
st.title("📊 Dashboard Fundamentus")
st.markdown(f"Exibindo **{len(df_filtrado)}** ativos com score ≥ **{min_score}**")

tab1, tab2, tab3 = st.tabs(["📈 Visão Geral", "📊 Indicadores", "📌 Comparar Ativos"])

# --- Tab 1: Visão Geral
with tab1:
    st.subheader("Top ações por score")
    st.dataframe(df_filtrado.head(top_n), use_container_width=True)

    col1, col2 = st.columns(2)
    with col1:
        fig = px.histogram(df_filtrado, x="score", nbins=20, title="Distribuição dos Scores", color_discrete_sequence=["#636EFA"])
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        fig = px.bar(df_filtrado.head(top_n), x="papel", y="score", title="Top ações por Score", text="score", color="score")
        st.plotly_chart(fig, use_container_width=True)

# --- Tab 2: Indicadores
with tab2:
    st.subheader("📊 Análise de Indicadores Fundamentais")
    st.markdown("Explore a distribuição dos principais indicadores para as ações filtradas:")

    indicadores = {
        "p_l": "P/L (Preço / Lucro)",
        "p_vp": "P/VP (Preço / Valor Patrimonial)",
        "psr": "PSR (Preço / Receita)",
        "dividend_yield": "Dividend Yield (%)",
        "roe": "ROE (%)",
        "roic": "ROIC (%)"
    }

    tipo_grafico = st.radio("Escolha o tipo de gráfico:", ["Boxplot", "Histograma"], horizontal=True)
    escala = st.selectbox("Escala do eixo Y:", ["Linear", "Logarítmica"])

    col1, col2 = st.columns(2)

    for i, (col, label) in enumerate(indicadores.items()):
        container = col1 if i % 2 == 0 else col2
        with container:
            with st.expander(f"📈 {label}"):
                if tipo_grafico == "Boxplot":
                    fig = px.box(df_filtrado, y=col, points="outliers", title=label)
                else:
                    fig = px.histogram(df_filtrado, x=col, nbins=30, title=label)

                fig.update_layout(yaxis_type="linear" if escala == "Linear" else "log")
                fig.update_layout(margin=dict(l=20, r=20, t=30, b=20))
                st.plotly_chart(fig, use_container_width=True)


# --- Tab 3: Comparar Ativos
with tab3:
    ativos_selecionados = st.multiselect("Escolha até 5 papéis para comparar", df_filtrado["papel"].unique(), max_selections=5)

    if ativos_selecionados:
        colunas_radar = ["p_l", "p_vp", "psr", "dividend_yield", "roe", "roic"]
        df_radar = df_filtrado[df_filtrado["papel"].isin(ativos_selecionados)][["papel"] + colunas_radar].set_index("papel")

        fig = go.Figure()
        for papel in df_radar.index:
            fig.add_trace(go.Scatterpolar(
                r=df_radar.loc[papel].values,
                theta=colunas_radar,
                fill='toself',
                name=papel
            ))
        fig.update_layout(
            polar=dict(radialaxis=dict(visible=True)),
            title="Comparação de Indicadores",
            showlegend=True
        )
        st.plotly_chart(fig, use_container_width=True)

def extrair_papeis(prompt, df):
    papeis_disponiveis = df["papel"].str.upper().tolist()
    return [p for p in papeis_disponiveis if p in prompt.upper()

def montar_contexto_para_papeis(papeis, df):
    dados = df[df["papel"].isin(papeis)]
    return dados.to_dict(orient="records")

# Auxiliar AI (Chatbot)
with st.expander("Auxilia AI"):
    # Entrada do usuário para interação com o chatbot
    prompt = st.chat_input("Escreva alguma coisa")
    prompt_aux = prompt
    
    if prompt:
        papeis_encontrados = extrair_papeis(prompt, df)
        if papeis_encontrados:
            dados = montar_contexto_para_papeis(papeis_encontrados, df)
            # Substitui a palavra 'base' pela representação em string do DataFrame
            prompt = f"{prompt} com esses dados: {dados}"
        
        # Exibe a mensagem do usuário
        st.write(f"Usuario: {prompt_aux}")
        
        # Gera a resposta do chatbot e a exibe
        resposta = mensagem_cli(prompt)
        if resposta:
            st.write(f"Auxilia AI: {resposta}")