import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from processar_fundamentus import resultado

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
    indicadores = ["p_l", "p_vp", "psr", "dividend_yield", "roe", "roic"]
    st.subheader("Distribuição de Indicadores")

    for indicador in indicadores:
        with st.expander(f"📌 {indicador.upper()}"):
            fig = px.box(df_filtrado, y=indicador, title=f"Distribuição de {indicador.upper()}")
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
