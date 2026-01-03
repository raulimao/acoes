"""
Application Settings and Constants
"""
import os
from dotenv import load_dotenv

load_dotenv()

# =================================================================
#                     CONFIGURAÇÕES PRINCIPAIS
# =================================================================

# Groq AI
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_MODEL = "compound-beta"

# Supabase (a configurar)
SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY", "")

# Fundamentus
FUNDAMENTUS_URL = "https://www.fundamentus.com.br/resultado.php"
FUNDAMENTUS_DETAIL_URL = "https://www.fundamentus.com.br/detalhes.php?papel="

# Blacklist de ativos
BLACKLIST_ATIVOS = ['MRSA6B', 'MRSA5B', 'MRSA3B']

# =================================================================
#                     CONFIGURAÇÕES DE HISTÓRICO
# =================================================================
SCORE_MINIMO_HISTORICO = 8.0  # Ação só será salva se Super Score >= este valor

COLUNAS_HISTORICO = [
    'papel', 'setor', 'subsetor', 'cotacao', 'p_l', 'p_vp', 'psr', 
    'dividend_yield', 'p_ativo', 'p_cap_giro', 'p_ebit', 'p_ativo_circulante_liq',
    'ev_ebit', 'ev_ebitda', 'margem_ebit', 'margem_liquida', 'liquidez_corrente',
    'roic', 'roe', 'liquidez_2meses', 'patrimonio_liquido', 'div_bruta_patrimonio',
    'crescimento_receita_5a', 'score_graham', 'score_greenblatt', 'score_bazin',
    'score_qualidade', 'super_score'
]
