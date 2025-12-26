"""
Custom CSS Styles for Premium Dashboard Look
Includes: Gradients, Glassmorphism, Animations, Modern Typography
"""

CUSTOM_CSS = """
<style>
    /* ============================================
       IMPORTS & FONTS
    ============================================ */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');
    @import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;600;700&display=swap');
    
    /* ============================================
       ROOT VARIABLES
    ============================================ */
    :root {
        --primary: #00D4FF;
        --primary-dark: #0099CC;
        --secondary: #7B2DFF;
        --accent: #FF6B6B;
        --success: #00F5A0;
        --warning: #FFD93D;
        --bg-dark: #0a0a0f;
        --bg-card: rgba(26, 26, 46, 0.7);
        --glass: rgba(255, 255, 255, 0.05);
        --glass-border: rgba(255, 255, 255, 0.1);
        --gradient-1: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        --gradient-2: linear-gradient(135deg, #00D4FF 0%, #7B2DFF 100%);
        --gradient-3: linear-gradient(135deg, #00F5A0 0%, #00D4FF 100%);
        --gradient-hero: linear-gradient(135deg, #0a0a0f 0%, #1a1a2e 50%, #16213e 100%);
    }
    
    /* ============================================
       ANIMATED BACKGROUND
    ============================================ */
    .stApp {
        background: var(--gradient-hero) !important;
        background-attachment: fixed !important;
        font-family: 'Inter', sans-serif !important;
    }
    
    .stApp::before {
        content: '';
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background: 
            radial-gradient(ellipse at 20% 20%, rgba(0, 212, 255, 0.15) 0%, transparent 50%),
            radial-gradient(ellipse at 80% 80%, rgba(123, 45, 255, 0.15) 0%, transparent 50%),
            radial-gradient(ellipse at 50% 50%, rgba(0, 245, 160, 0.05) 0%, transparent 60%);
        pointer-events: none;
        z-index: -1;
        animation: pulseGlow 8s ease-in-out infinite;
    }
    
    @keyframes pulseGlow {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.7; }
    }
    
    /* ============================================
       HEADER & TITLES
    ============================================ */
    .stApp h1 {
        font-family: 'Space Grotesk', sans-serif !important;
        background: var(--gradient-2);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        font-weight: 700 !important;
        letter-spacing: -0.02em;
        margin-bottom: 1rem !important;
    }
    
    .stApp h2 {
        font-family: 'Space Grotesk', sans-serif !important;
        color: #fff !important;
        font-weight: 600 !important;
        border-bottom: 2px solid var(--primary);
        padding-bottom: 0.5rem;
        margin-top: 2rem !important;
    }
    
    .stApp h3 {
        color: var(--primary) !important;
        font-weight: 500 !important;
    }
    
    /* ============================================
       SIDEBAR - GLASSMORPHISM
    ============================================ */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, rgba(10, 10, 15, 0.95) 0%, rgba(26, 26, 46, 0.95) 100%) !important;
        backdrop-filter: blur(20px) !important;
        border-right: 1px solid var(--glass-border) !important;
    }
    
    [data-testid="stSidebar"] > div:first-child {
        background: transparent !important;
    }
    
    [data-testid="stSidebar"] .stMarkdown h2 {
        background: var(--gradient-3);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-align: center;
        font-size: 1.5rem !important;
    }
    
    /* ============================================
       CARDS & EXPANDERS - GLASSMORPHISM
    ============================================ */
    .stExpander {
        background: var(--glass) !important;
        border: 1px solid var(--glass-border) !important;
        border-radius: 16px !important;
        backdrop-filter: blur(10px) !important;
        overflow: hidden;
        transition: all 0.3s ease !important;
    }
    
    .stExpander:hover {
        border-color: var(--primary) !important;
        box-shadow: 0 8px 32px rgba(0, 212, 255, 0.15) !important;
        transform: translateY(-2px);
    }
    
    [data-testid="stExpander"] details summary {
        font-weight: 500 !important;
        color: #fff !important;
    }
    
    /* ============================================
       TABS - MODERN STYLE
    ============================================ */
    .stTabs [data-baseweb="tab-list"] {
        background: var(--glass) !important;
        border-radius: 12px !important;
        padding: 8px !important;
        gap: 8px !important;
        border: 1px solid var(--glass-border) !important;
    }
    
    .stTabs [data-baseweb="tab"] {
        background: transparent !important;
        border-radius: 8px !important;
        color: rgba(255, 255, 255, 0.6) !important;
        font-weight: 500 !important;
        transition: all 0.3s ease !important;
        padding: 12px 24px !important;
    }
    
    .stTabs [data-baseweb="tab"]:hover {
        background: rgba(0, 212, 255, 0.1) !important;
        color: var(--primary) !important;
    }
    
    .stTabs [aria-selected="true"] {
        background: var(--gradient-2) !important;
        color: white !important;
        font-weight: 600 !important;
        box-shadow: 0 4px 20px rgba(0, 212, 255, 0.3) !important;
    }
    
    /* ============================================
       BUTTONS - GRADIENT & GLOW
    ============================================ */
    .stButton > button {
        background: var(--gradient-2) !important;
        border: none !important;
        border-radius: 12px !important;
        padding: 12px 32px !important;
        font-weight: 600 !important;
        font-size: 1rem !important;
        color: white !important;
        transition: all 0.3s ease !important;
        box-shadow: 0 4px 20px rgba(0, 212, 255, 0.3) !important;
    }
    
    .stButton > button:hover {
        transform: translateY(-3px) !important;
        box-shadow: 0 8px 30px rgba(0, 212, 255, 0.5) !important;
    }
    
    .stButton > button:active {
        transform: translateY(0) !important;
    }
    
    /* Primary button variant */
    .stButton > button[kind="primary"] {
        background: var(--gradient-3) !important;
    }
    
    /* ============================================
       INPUTS - MODERN DARK
    ============================================ */
    .stTextInput > div > div > input,
    .stNumberInput > div > div > input,
    .stSelectbox > div > div > div {
        background: rgba(255, 255, 255, 0.05) !important;
        border: 1px solid var(--glass-border) !important;
        border-radius: 10px !important;
        color: white !important;
        padding: 12px 16px !important;
        transition: all 0.3s ease !important;
    }
    
    .stTextInput > div > div > input:focus,
    .stNumberInput > div > div > input:focus {
        border-color: var(--primary) !important;
        box-shadow: 0 0 0 2px rgba(0, 212, 255, 0.2) !important;
    }
    
    /* ============================================
       SLIDERS - GRADIENT TRACK
    ============================================ */
    .stSlider > div > div > div > div {
        background: var(--gradient-2) !important;
    }
    
    .stSlider > div > div > div > div > div {
        background: white !important;
        border: 2px solid var(--primary) !important;
        box-shadow: 0 0 10px var(--primary) !important;
    }
    
    /* ============================================
       DATAFRAME - DARK THEME
    ============================================ */
    .stDataFrame {
        border-radius: 16px !important;
        overflow: hidden !important;
        border: 1px solid var(--glass-border) !important;
    }
    
    .stDataFrame [data-testid="stDataFrameResizable"] {
        background: rgba(10, 10, 15, 0.8) !important;
    }
    
    /* ============================================
       METRICS - CARD STYLE
    ============================================ */
    [data-testid="stMetric"] {
        background: var(--glass) !important;
        border: 1px solid var(--glass-border) !important;
        border-radius: 16px !important;
        padding: 20px !important;
        backdrop-filter: blur(10px) !important;
    }
    
    [data-testid="stMetricValue"] {
        background: var(--gradient-2);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-weight: 700 !important;
        font-size: 2rem !important;
    }
    
    /* ============================================
       ALERTS & MESSAGES
    ============================================ */
    .stAlert {
        border-radius: 12px !important;
        border: none !important;
        backdrop-filter: blur(10px) !important;
    }
    
    .stSuccess {
        background: rgba(0, 245, 160, 0.15) !important;
        border-left: 4px solid var(--success) !important;
    }
    
    .stWarning {
        background: rgba(255, 217, 61, 0.15) !important;
        border-left: 4px solid var(--warning) !important;
    }
    
    .stError {
        background: rgba(255, 107, 107, 0.15) !important;
        border-left: 4px solid var(--accent) !important;
    }
    
    .stInfo {
        background: rgba(0, 212, 255, 0.15) !important;
        border-left: 4px solid var(--primary) !important;
    }
    
    /* ============================================
       PLOTLY CHARTS
    ============================================ */
    .js-plotly-plot {
        border-radius: 16px !important;
        overflow: hidden !important;
    }
    
    /* ============================================
       MULTISELECT - TAGS
    ============================================ */
    .stMultiSelect [data-baseweb="tag"] {
        background: var(--gradient-2) !important;
        border-radius: 8px !important;
    }
    
    /* ============================================
       DIVIDER
    ============================================ */
    hr {
        border: none !important;
        height: 1px !important;
        background: linear-gradient(90deg, transparent, var(--primary), var(--secondary), transparent) !important;
        margin: 2rem 0 !important;
    }
    
    /* ============================================
       SCROLLBAR - CUSTOM
    ============================================ */
    ::-webkit-scrollbar {
        width: 8px;
        height: 8px;
    }
    
    ::-webkit-scrollbar-track {
        background: var(--bg-dark);
    }
    
    ::-webkit-scrollbar-thumb {
        background: var(--gradient-2);
        border-radius: 4px;
    }
    
    ::-webkit-scrollbar-thumb:hover {
        background: var(--primary);
    }
    
    /* ============================================
       LOGIN PAGE SPECIFIC
    ============================================ */
    [data-testid="stForm"] {
        background: var(--glass) !important;
        border: 1px solid var(--glass-border) !important;
        border-radius: 24px !important;
        padding: 40px !important;
        backdrop-filter: blur(20px) !important;
        box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3) !important;
    }
    
    /* ============================================
       FLOATING ANIMATION
    ============================================ */
    @keyframes float {
        0%, 100% { transform: translateY(0px); }
        50% { transform: translateY(-10px); }
    }
    
    .floating {
        animation: float 3s ease-in-out infinite;
    }
    
    /* ============================================
       GRADIENT TEXT UTILITY
    ============================================ */
    .gradient-text {
        background: var(--gradient-2);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
    }
    
    /* ============================================
       HIDE STREAMLIT BRANDING
    ============================================ */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* ============================================
       CHAT INPUT
    ============================================ */
    .stChatInput > div {
        background: var(--glass) !important;
        border: 1px solid var(--glass-border) !important;
        border-radius: 16px !important;
    }
    
    .stChatInput textarea {
        background: transparent !important;
        color: white !important;
    }
</style>
"""

LOGIN_PAGE_EXTRA_CSS = """
<style>
    /* Login page hero section */
    .login-hero {
        text-align: center;
        padding: 40px 20px;
        margin-bottom: 30px;
    }
    
    .login-hero h1 {
        font-size: 3rem !important;
        margin-bottom: 1rem !important;
    }
    
    .login-hero p {
        color: rgba(255, 255, 255, 0.7);
        font-size: 1.2rem;
        max-width: 500px;
        margin: 0 auto;
    }
    
    .login-logo {
        font-size: 4rem;
        margin-bottom: 1rem;
        display: block;
        animation: float 3s ease-in-out infinite;
    }
    
    .feature-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
        gap: 20px;
        margin-top: 40px;
    }
    
    .feature-card {
        background: rgba(255, 255, 255, 0.05);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 16px;
        padding: 24px;
        text-align: center;
        transition: all 0.3s ease;
    }
    
    .feature-card:hover {
        background: rgba(0, 212, 255, 0.1);
        border-color: var(--primary);
        transform: translateY(-5px);
    }
    
    .feature-icon {
        font-size: 2.5rem;
        margin-bottom: 12px;
    }
    
    .feature-title {
        font-weight: 600;
        color: white;
        margin-bottom: 8px;
    }
    
    .feature-desc {
        color: rgba(255, 255, 255, 0.6);
        font-size: 0.9rem;
    }
</style>
"""


def inject_custom_css():
    """Inject custom CSS into Streamlit app."""
    import streamlit as st
    st.markdown(CUSTOM_CSS, unsafe_allow_html=True)


def inject_login_css():
    """Inject login page specific CSS."""
    import streamlit as st
    st.markdown(LOGIN_PAGE_EXTRA_CSS, unsafe_allow_html=True)


def render_login_hero():
    """Render beautiful login hero section."""
    import streamlit as st
    
    st.markdown("""
    <div class="login-hero">
        <span class="login-logo">📊</span>
        <h1>TopAcões</h1>
        <p>Análise fundamentalista inteligente para investidores que buscam as melhores oportunidades na B3</p>
    </div>
    """, unsafe_allow_html=True)


def render_features_grid():
    """Render features grid for login page."""
    import streamlit as st
    
    st.markdown("""
    <div class="feature-grid">
        <div class="feature-card">
            <div class="feature-icon">🎯</div>
            <div class="feature-title">4 Estratégias</div>
            <div class="feature-desc">Graham, Greenblatt, Bazin e Qualidade</div>
        </div>
        <div class="feature-card">
            <div class="feature-icon">📈</div>
            <div class="feature-title">Super Score</div>
            <div class="feature-desc">Ranking inteligente de ações</div>
        </div>
        <div class="feature-card">
            <div class="feature-icon">🤖</div>
            <div class="feature-title">IA Integrada</div>
            <div class="feature-desc">Consultor virtual de investimentos</div>
        </div>
        <div class="feature-card">
            <div class="feature-icon">📜</div>
            <div class="feature-title">Histórico</div>
            <div class="feature-desc">Acompanhe a evolução dos ativos</div>
        </div>
    </div>
    """, unsafe_allow_html=True)
