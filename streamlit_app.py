import logging
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from processar_fundamentus import resultado
from src.chat import mensagem_cli
from gtts import gTTS
import streamlit_authenticator as stauth
import yaml
from database import add_user, get_user, initialize_database

# --- Logging ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# --- Página ---
st.set_page_config(page_title="Dashboard Fundamentus", layout="wide")

# --- Configuração YAML ---
try:
    with open("config.yaml") as file:
        config = yaml.load(file, Loader=yaml.SafeLoader)
except Exception as e:
    st.error(f"Erro ao carregar config.yaml: {e}")
    st.stop()

# --- Inicializa banco e carrega usuários ---
conn, cursor = initialize_database()
cursor.execute("SELECT username, name, email, password FROM users")
users_data = cursor.fetchall()
conn.close()

credentials = {"usernames": {}}
for username, name, email, hashed_password in users_data:
    credentials["usernames"][username] = {
        "name": name,
        "email": email,
        "password": hashed_password.decode() if isinstance(hashed_password, bytes) else hashed_password
    }

# --- Autenticação ---
authenticator = stauth.Authenticate(
    credentials,
    config["cookie"]["name"],
    config["cookie"]["key"],
    config["cookie"]["expiry_days"]
)

# --- Login ---
name, authentication_status, username = authenticator.login(location="sidebar", form_name="Login")

# --- Status de login ---
if authentication_status is False:
    st.error("Usuário/Senha inválido!")
elif authentication_status is None:
    st.warning("Por favor, insira usuário e senha.")
    with st.expander("👤 Criar novo usuário"):
        new_username = st.text_input("Usuário")
        new_name = st.text_input("Nome completo")
        new_email = st.text_input("Email")
        new_password = st.text_input("Senha", type="password")
        confirm_password = st.text_input("Confirmar senha", type="password")
        if st.button("Cadastrar"):
            if new_password != confirm_password:
                st.error("As senhas não coincidem!")
            elif get_user(new_username):
                st.error("Usuário já existe!")
            else:
                add_user(new_username, new_name, new_email, new_password)
                st.success("Usuário criado com sucesso! Atualize a página.")

# --- Usuário autenticado ---
if authentication_status:
    st.title(f"Bem-vindo, {name}!")
    if st.sidebar.button("Logout"):
        authenticator.logout()
        st.rerun()

    df = resultado()

    # --- Filtros ---
    st.sidebar.header("🔎 Filtros")
    with st.sidebar.expander("🎯 Filtros de Pontuação", expanded=True):
        min_score = st.slider("Score mínimo", 0, 100, 60)
        max_score = st.slider("Score máximo", 0, 100, 100)
        df_filtrado = df[(df["score"] >= min_score) & (df["score"] <= max_score)]

    with st.sidebar.expander("📊 Ordenação"):
        colunas_numericas = df.select_dtypes(include=np.number).columns.tolist()
        coluna_ordenacao = st.selectbox("Ordenar por", colunas_numericas, index=colunas_numericas.index("score"))
        ordem = st.radio("Ordem", ["Decrescente", "Crescente"], horizontal=True)
        df_filtrado = df_filtrado.sort_values(by=coluna_ordenacao, ascending=(ordem == "Crescente"))

    with st.sidebar.expander("📈 Ações"):
        setores = sorted(df["papel"].str[:4].unique())
        prefixos = st.multiselect("Filtrar prefixo (ex: VALE, PETR)", setores)
        if prefixos:
            df_filtrado = df_filtrado[df_filtrado["papel"].str[:4].isin(prefixos)]

    with st.sidebar.expander("🔝 Exibição"):
        top_n = st.slider("Top N ativos", 5, 100, 10)

    # --- Layout principal ---
    st.title("📊 Dashboard Fundamentus")
    st.markdown(f"Exibindo **{len(df_filtrado)}** ativos com score ≥ **{min_score}**")

    tab1, tab2, tab3 = st.tabs(["📈 Visão Geral", "📊 Indicadores", "📌 Comparar Ativos"])

    with tab1:
        st.subheader("Top ações por score")
        st.dataframe(df_filtrado.head(top_n), use_container_width=True)
        col1, col2 = st.columns(2)
        with col1:
            fig = px.histogram(df_filtrado, x="score", nbins=20, title="Distribuição dos Scores")
            st.plotly_chart(fig, use_container_width=True)
        with col2:
            fig = px.bar(df_filtrado.head(top_n), x="papel", y="score", text="score", color="score", title="Top ações por Score")
            st.plotly_chart(fig, use_container_width=True)

    with tab2:
        st.subheader("📊 Indicadores Fundamentais")
        indicadores = {
            "p_l": "P/L",
            "p_vp": "P/VP",
            "psr": "PSR",
            "dividend_yield": "Dividend Yield",
            "roe": "ROE",
            "roic": "ROIC"
        }
        tipo = st.radio("Gráfico", ["Boxplot", "Histograma"], horizontal=True)
        escala = st.selectbox("Escala Y", ["Linear", "Logarítmica"])
        col1, col2 = st.columns(2)
        for i, (col, label) in enumerate(indicadores.items()):
            with (col1 if i % 2 == 0 else col2):
                with st.expander(label):
                    if tipo == "Boxplot":
                        fig = px.box(df_filtrado, y=col, points="outliers", title=label)
                    else:
                        fig = px.histogram(df_filtrado, x=col, nbins=30, title=label)
                    fig.update_layout(yaxis_type="linear" if escala == "Linear" else "log")
                    st.plotly_chart(fig, use_container_width=True)

    with tab3:
        st.subheader("📌 Comparar Ativos")
        selecionados = st.multiselect("Escolha até 5 papéis", df_filtrado["papel"].unique(), max_selections=5)
        if selecionados:
            colunas = ["p_l", "p_vp", "psr", "dividend_yield", "roe", "roic"]
            df_radar = df_filtrado[df_filtrado["papel"].isin(selecionados)][["papel"] + colunas].set_index("papel")
            fig = go.Figure()
            for papel in df_radar.index:
                fig.add_trace(go.Scatterpolar(r=df_radar.loc[papel], theta=colunas, fill='toself', name=papel))
            fig.update_layout(polar=dict(radialaxis=dict(visible=True)), showlegend=True)
            st.plotly_chart(fig, use_container_width=True)

    # --- Chat AI ---
    def extrair_papeis(prompt, df):
        return [p for p in df["papel"].str.upper() if p in prompt.upper()]

    def montar_contexto(papeis, df):
        return df[df["papel"].isin(papeis)].to_dict(orient="records")

    with st.expander("🧠 Auxilia AI"):
        prompt = st.chat_input("Digite sua pergunta")
        if prompt:
            papeis = extrair_papeis(prompt, df)
            if papeis:
                dados = montar_contexto(papeis, df)
                prompt += f" com esses dados: {dados}"
            st.write(f"Usuário: {prompt}")
            resposta = mensagem_cli(prompt)
            if resposta:
                st.write(f"Auxilia AI: {resposta}")
                tts = gTTS(text=resposta, lang="pt-br")
                tts.save("audio.mp3")
                st.audio("audio.mp3", format="audio/mp3")
