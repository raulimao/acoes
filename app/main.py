"""
Fundamentus Dashboard - Main Streamlit Application
"""
import sys
from pathlib import Path

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

import logging
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import streamlit_authenticator as stauth
import yaml
from gtts import gTTS

from core.pipeline import carregar_dados_completos
from services.auth_service import get_all_users, add_user, get_user, initialize_database
from services.ai_chat import processar_pergunta
from services.history_service import save_to_historico, get_historico
from config.strategies_config import ESTRATEGIAS
from config.settings import SCORE_MINIMO_HISTORICO
from app.styles import inject_custom_css, inject_login_css, render_login_hero, render_features_grid

# --- Logging ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# --- Page Config ---
st.set_page_config(
    page_title="TopAc̃ões | Dashboard Fundamentalista",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- Inject Custom CSS ---
inject_custom_css()

# --- Load config.yaml ---
CONFIG_PATH = Path(__file__).parent.parent / "config.yaml"
try:
    with open(CONFIG_PATH) as file:
        config = yaml.load(file, Loader=yaml.SafeLoader)
except Exception as e:
    st.error(f"Erro ao carregar config.yaml: {e}")
    st.stop()

# --- Initialize database and load users ---
initialize_database()
credentials = get_all_users()

# --- Authentication ---
authenticator = stauth.Authenticate(
    credentials,
    config["cookie"]["name"],
    config["cookie"]["key"],
    config["cookie"]["expiry_days"]
)

# --- Login ---
authenticator.login(location="sidebar")

# Get auth status from session_state (v0.4.x API)
name = st.session_state.get("name")
authentication_status = st.session_state.get("authentication_status")
username = st.session_state.get("username")

# --- User Registration (before auth) ---
if authentication_status is None:
    inject_login_css()
    render_login_hero()
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        with st.expander("👤 Criar nova conta", expanded=False):
            new_username = st.text_input("👤 Usuário", placeholder="Digite seu usuário")
            new_name = st.text_input("📝 Nome completo", placeholder="Seu nome")
            new_email = st.text_input("📧 Email", placeholder="seu@email.com")
            new_password = st.text_input("🔒 Senha", type="password", placeholder="********")
            confirm_password = st.text_input("🔁 Confirmar senha", type="password", placeholder="********")

            if st.button("🚀 Cadastrar", use_container_width=True):
                if not all([new_username, new_name, new_email, new_password, confirm_password]):
                    st.error("⚠️ Preencha todos os campos.")
                elif new_password != confirm_password:
                    st.error("❌ As senhas não coincidem!")
                elif get_user(new_username):
                    st.error("⚠️ Usuário já existe!")
                else:
                    add_user(new_username, new_name, new_email, new_password)
                    st.success("✅ Conta criada com sucesso! Faça login na barra lateral.")
    
    render_features_grid()
    st.stop()

# --- Login failed ---
if authentication_status is False:
    inject_login_css()
    render_login_hero()
    st.error("❌ Usuário ou senha inválidos!")
    render_features_grid()
    st.stop()

# --- Authenticated User ---
if authentication_status:
    # Dashboard header with gradient
    st.markdown(f"""
    <div style="display: flex; align-items: center; gap: 15px; margin-bottom: 20px;">
        <span style="font-size: 3rem;">📊</span>
        <div>
            <h1 style="margin: 0; font-size: 2.5rem;">Olá, {name}!</h1>
            <p style="margin: 0; color: rgba(255,255,255,0.6);">Bem-vindo ao seu painel de análise fundamentalista</p>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Logout button in sidebar
    with st.sidebar:
        st.markdown("### 📊 TopAc̃ões")
        st.divider()
        if authenticator.logout(button_name="🚪 Sair"):
            st.session_state.clear()
            st.rerun()

    # Load data
    df = carregar_dados_completos()

    # --- Sidebar Filters ---
    st.sidebar.header("🔎 Filtros")
    
    with st.sidebar.expander("🎯 Filtros de Pontuação", expanded=True):
        min_score = st.slider("Super Score mínimo", 0.0, 20.0, 5.0, 0.5)
        max_score = st.slider("Super Score máximo", 0.0, 20.0, 20.0, 0.5)
        df_filtrado = df[(df["super_score"] >= min_score) & (df["super_score"] <= max_score)]

    with st.sidebar.expander("📊 Ordenação"):
        colunas_numericas = df.select_dtypes(include=np.number).columns.tolist()
        coluna_ordenacao = st.selectbox("Ordenar por", colunas_numericas, index=colunas_numericas.index("super_score") if "super_score" in colunas_numericas else 0)
        ordem = st.radio("Ordem", ["Decrescente", "Crescente"], horizontal=True)
        df_filtrado = df_filtrado.sort_values(by=coluna_ordenacao, ascending=(ordem == "Crescente"))

    with st.sidebar.expander("🏢 Setores"):
        if 'setor' in df.columns:
            setores_unicos = sorted(df[df['setor'] != 'N/A']['setor'].unique())
            setores_selecionados = st.multiselect("Filtrar por Setor", setores_unicos)
            if setores_selecionados:
                df_filtrado = df_filtrado[df_filtrado['setor'].isin(setores_selecionados)]
        
        if 'subsetor' in df.columns:
            subsetores_unicos = sorted(df_filtrado[df_filtrado['subsetor'] != 'N/A']['subsetor'].unique())
            subsetores_selecionados = st.multiselect("Filtrar por Subsetor", subsetores_unicos)
            if subsetores_selecionados:
                df_filtrado = df_filtrado[df_filtrado['subsetor'].isin(subsetores_selecionados)]

    with st.sidebar.expander("📈 Ações"):
        if 'papel' in df.columns:
            prefixos_unicos = sorted(df["papel"].str[:4].unique())
            prefixos = st.multiselect("Filtrar prefixo (ex: VALE, PETR)", prefixos_unicos)
            if prefixos:
                df_filtrado = df_filtrado[df_filtrado["papel"].str[:4].isin(prefixos)]

    with st.sidebar.expander("🔝 Exibição"):
        top_n = st.slider("Top N ativos", 5, 100, 10)

    st.header("📊 Dashboard Fundamentus")
    st.markdown(f"Exibindo **{len(df_filtrado)}** ativos com Super Score ≥ **{min_score}**")

    # --- Tabs ---
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["📈 Visão Geral", "🎯 Estratégias", "📊 Indicadores", "📌 Comparar Ativos", "📜 Histórico"])

    # Tab 1: Overview
    with tab1:
        st.subheader("Top ações por Super Score")
        
        # Select columns to display (including sector)
        cols_display = ['papel', 'setor', 'cotacao', 'p_l', 'p_vp', 'dividend_yield', 'roe', 'roic', 
                       'score_graham', 'score_greenblatt', 'score_bazin', 'score_qualidade', 'super_score']
        cols_available = [c for c in cols_display if c in df_filtrado.columns]
        
        st.dataframe(df_filtrado[cols_available].head(top_n), use_container_width=True)
        
        col1, col2 = st.columns(2)
        with col1:
            fig = px.histogram(df_filtrado, x="super_score", nbins=20, title="Distribuição dos Super Scores")
            st.plotly_chart(fig, use_container_width=True)
        with col2:
            fig = px.bar(df_filtrado.head(top_n), x="papel", y="super_score", text="super_score", 
                        color="super_score", title="Top ações por Super Score")
            st.plotly_chart(fig, use_container_width=True)

    # Tab 2: Strategies
    with tab2:
        st.subheader("🎯 Scores por Estratégia de Investimento")
        
        # Strategy explanations
        for nome, config in ESTRATEGIAS.items():
            with st.expander(f"📌 {config['cabecalho']} (Peso: {config['peso']}x)"):
                st.write(f"**{config['descricao']}**")
                st.write(f"Filtros utilizados: {', '.join(config['filtros'])}")
        
        # Strategy comparison chart
        st.subheader("Comparação de Estratégias (Top 10)")
        
        top_10 = df_filtrado.head(10)
        if not top_10.empty:
            strategy_cols = [f'score_{nome}' for nome in ESTRATEGIAS.keys()]
            strategy_cols = [c for c in strategy_cols if c in top_10.columns]
            
            fig = go.Figure()
            for col in strategy_cols:
                fig.add_trace(go.Bar(name=col.replace('score_', '').title(), x=top_10['papel'], y=top_10[col]))
            
            fig.update_layout(barmode='group', title="Scores por Estratégia")
            st.plotly_chart(fig, use_container_width=True)

    # Tab 3: Indicators
    with tab3:
        st.subheader("📊 Indicadores Fundamentais")
        indicadores = {
            "p_l": "P/L", "p_vp": "P/VP", "psr": "PSR", "dividend_yield": "Dividend Yield",
            "roe": "ROE", "roic": "ROIC"
        }
        tipo = st.radio("Gráfico", ["Boxplot", "Histograma"], horizontal=True)
        escala = st.selectbox("Escala Y", ["Linear", "Logarítmica"])
        
        col1, col2 = st.columns(2)
        for i, (col, label) in enumerate(indicadores.items()):
            if col in df_filtrado.columns:
                with (col1 if i % 2 == 0 else col2):
                    with st.expander(label):
                        if tipo == "Boxplot":
                            fig = px.box(df_filtrado, y=col, points="outliers", title=label)
                        else:
                            fig = px.histogram(df_filtrado, x=col, nbins=30, title=label)
                        fig.update_layout(yaxis_type="linear" if escala == "Linear" else "log")
                        st.plotly_chart(fig, use_container_width=True)

    # Tab 4: Compare Assets
    with tab4:
        st.subheader("📌 Comparar Ativos")
        if 'papel' in df_filtrado.columns:
            selecionados = st.multiselect("Escolha até 5 papéis", df_filtrado["papel"].unique(), max_selections=5)
            if selecionados:
                colunas_radar = ['p_l', 'p_vp', 'dividend_yield', 'roe', 'roic', 'liquidez_corrente']
                colunas_radar = [c for c in colunas_radar if c in df_filtrado.columns]
                
                df_radar = df_filtrado[df_filtrado["papel"].isin(selecionados)][["papel"] + colunas_radar].set_index("papel")
                
                fig = go.Figure()
                for papel in df_radar.index:
                    fig.add_trace(go.Scatterpolar(r=df_radar.loc[papel], theta=colunas_radar, fill='toself', name=papel))
                fig.update_layout(polar=dict(radialaxis=dict(visible=True)), showlegend=True)
                st.plotly_chart(fig, use_container_width=True)

    # Tab 5: History
    with tab5:
        st.subheader("📜 Histórico de Ações Qualificadas")
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            score_min_hist = st.number_input(
                "Score mínimo para salvar",
                min_value=0.0,
                max_value=20.0,
                value=SCORE_MINIMO_HISTORICO,
                step=0.5
            )
        
        with col2:
            if st.button("💾 Salvar Ações Qualificadas", type="primary"):
                count = save_to_historico(df, score_minimo=score_min_hist)
                if count > 0:
                    st.success(f"✅ {count} ações salvas no histórico!")
                else:
                    st.warning("Nenhuma ação qualificada ou erro ao salvar.")
        
        st.divider()
        
        # Display history
        st.subheader("📋 Histórico Salvo")
        
        dias_filtro = st.slider("Últimos N dias", 1, 90, 30)
        
        df_hist = get_historico(dias=dias_filtro)
        
        if not df_hist.empty:
            st.markdown(f"**{len(df_hist)}** registros encontrados nos últimos **{dias_filtro}** dias")
            
            # Show columns
            cols_hist = ['data', 'papel', 'cotacao', 'super_score', 'score_graham', 'score_greenblatt', 'score_bazin', 'score_qualidade']
            cols_hist = [c for c in cols_hist if c in df_hist.columns]
            
            st.dataframe(df_hist[cols_hist], use_container_width=True)
            
            # Chart: Super Score over time for top stocks
            if 'papel' in df_hist.columns and 'super_score' in df_hist.columns:
                top_papeis = df_hist.groupby('papel')['super_score'].mean().nlargest(5).index.tolist()
                df_top = df_hist[df_hist['papel'].isin(top_papeis)]
                
                if not df_top.empty:
                    fig = px.line(df_top, x='data', y='super_score', color='papel', 
                                 title="Evolução do Super Score (Top 5)")
                    st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("📭 Nenhum histórico encontrado. Clique em 'Salvar Ações Qualificadas' para começar.")

    # --- AI Chat ---
    with st.expander("🧠 Auxilia AI"):
        prompt = st.chat_input("Digite sua pergunta")
        if prompt:
            st.write(f"Usuário: {prompt}")
            try:
                resposta = processar_pergunta(prompt, df)
                if resposta:
                    st.write(f"Auxilia AI: {resposta}")
                    
                    # Text-to-speech
                    audio_path = Path(__file__).parent.parent / "assets" / "audio" / "response.mp3"
                    audio_path.parent.mkdir(parents=True, exist_ok=True)
                    
                    tts = gTTS(text=resposta, lang="pt-br")
                    tts.save(str(audio_path))
                    st.audio(str(audio_path), format="audio/mp3")
            except Exception as e:
                st.error(f"Erro ao processar: {e}")
