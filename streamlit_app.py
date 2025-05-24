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

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


# --- Configuração da Página ---
st.set_page_config(page_title="Dashboard Fundamentus", layout="wide")

# --- Carrega config.yaml ---
try:
    with open('config.yaml') as file:
        config = yaml.load(file, Loader=yaml.Loader)
except FileNotFoundError:
    st.error("Erro: Arquivo config.yaml não encontrado. Certifique-se de que o arquivo está na raiz do projeto.")
    st.stop()
except yaml.YAMLError:
    st.error("Erro: O arquivo config.yaml contém um erro de sintaxe YAML. Verifique a formatação.")
# --- Prepara dados dos usuários salvos no banco ---
conn, cursor = initialize_database()
cursor.execute("SELECT username, name, email, password FROM users")
users_data = cursor.fetchall()
conn.close()

credentials = {"usernames": {}}
for user in users_data:
    username, name, email, hashed_password = user
    credentials["usernames"][username] = {
        "name": name,
        "email": email,
        "password": hashed_password.decode('utf-8')
    }

# --- Autenticação ---
authenticator = stauth.Authenticate(
    credentials,
    config['cookie']['name'],
    config['cookie']['key'],
    config['cookie']['expiry_days']
)

# ⚠️ Corrigir esta linha:
name, authentication_status, username = authenticator.login("Login", "main")

# --- Condicional baseada em autenticação ---
if authentication_status is False:
    st.error('Usuário/Senha é inválido!')

elif authentication_status is None:
    st.warning('Por favor, insira o usuário e senha!')
    # --- Cadastro de Novo Usuário (visível apenas quando não autenticado) ---
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
                st.success("Usuário criado com sucesso! Atualize a página para fazer login.")

# --- Conteúdo Autenticado (visível apenas quando autenticado) ---
if authentication_status:
    st.title(f'Bem vindo {name}!')
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
        coluna_numerica = df.select_dtypes(include=np.number).columns.tolist()
        coluna_ordenacao = st.selectbox("Ordenar por", coluna_numerica, index=coluna_numerica.index("score") if "score" in coluna_numerica else 0)
        ordem = st.radio("Ordem", ["Decrescente", "Crescente"], horizontal=True)
        crescente = ordem == "Crescente"
        df_filtrado = df_filtrado.sort_values(by=coluna_ordenacao, ascending=crescente)

    with st.sidebar.expander("📈 Seleção de Ações"):
        setores = sorted(df["papel"].str[:4].unique())
        prefixos = st.multiselect("Filtrar prefixo (ex: VALE, PETR)", setores)
        if prefixos:
            df_filtrado = df_filtrado[df_filtrado["papel"].str[:4].isin(prefixos)]

    with st.sidebar.expander("🔝 Exibição"):
        top_n = st.slider("Top N ativos", 5, 100, 10)

    # --- Layout Principal ---
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
            fig = px.bar(df_filtrado.head(top_n), x="papel", y="score", title="Top ações por Score", text="score", color="score")
            st.plotly_chart(fig, use_container_width=True)

    with tab2:
        st.subheader("📊 Análise de Indicadores Fundamentais")

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
                    st.plotly_chart(fig, use_container_width=True)

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

# --- Auxilia AI (Mova para dentro do bloco autenticado se quiser que só apareça após login) ---
# Se o chatbot for um recurso premium, mantenha-o dentro do if authentication_status:
# Se for um recurso público, mova-o para fora dos blocos condicionais de autenticação.
# Pelo contexto, parece ser um recurso premium, então mantive a estrutura atual.
# Se precisar mover, me diga!
    def extrair_papeis(prompt, df):
        papeis_disponiveis = df["papel"].str.upper().tolist()
        return [p for p in papeis_disponiveis if p in prompt.upper()]

    def montar_contexto_para_papeis(papeis, df):
        dados = df[df["papel"].isin(papeis)]
        return dados.to_dict(orient="records")

    with st.expander("🧠 Auxilia AI"):
        prompt = st.chat_input("Escreva alguma coisa")
        prompt_aux = prompt

        if prompt:
            papeis_encontrados = extrair_papeis(prompt, df)
            if papeis_encontrados:
                dados = montar_contexto_para_papeis(papeis_encontrados, df)
                prompt = f"{prompt} com esses dados: {dados}"

            st.write(f"Usuário: {prompt_aux}")
            resposta = mensagem_cli(prompt)
            if resposta:
                st.write(f"Auxilia AI: {resposta}")
                tts = gTTS(text=resposta, lang='pt-br')
                tts.save("audio.mp3")
                st.audio("audio.mp3", format="audio/mp3")
