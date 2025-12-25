"""
Strategies Configuration - Filters and Weights
Based on Google Sheets Script investment strategies
"""

# =================================================================
#      FILTROS COM SCORE GRADUAL E PESOS
# =================================================================

FILTROS = [
    {
        'nome': 'p_l',
        'cabecalho': 'Check P/L',
        'peso': 1.5,
        'condicao': lambda v: 0.0 if v <= 0 else 1.0 if v <= 6 else 0.7 if v <= 10 else 0.3 if v <= 15 else 0.0
    },
    {
        'nome': 'p_vp',
        'cabecalho': 'Check P/VP',
        'peso': 1.2,
        'condicao': lambda v: 0.0 if v <= 0 else 1.0 if v <= 1.0 else 0.6 if v <= 1.5 else 0.2 if v <= 2.0 else 0.0
    },
    {
        'nome': 'ev_ebit',
        'cabecalho': 'Check EV/EBIT',
        'peso': 1.5,
        'condicao': lambda v: 0.0 if v <= 0 else 1.0 if v <= 5 else 0.7 if v <= 8 else 0.3 if v <= 10 else 0.0
    },
    {
        'nome': 'dividend_yield',
        'cabecalho': 'Check DY',
        'peso': 1.0,
        'condicao': lambda v: 1.0 if v > 0.10 else 0.7 if v > 0.06 else 0.3 if v > 0.04 else 0.0
    },
    {
        'nome': 'roe',
        'cabecalho': 'Check ROE',
        'peso': 2.0,
        'condicao': lambda v: 1.0 if v > 0.20 else 0.8 if v > 0.15 else 0.4 if v > 0.10 else 0.0
    },
    {
        'nome': 'roic',
        'cabecalho': 'Check ROIC',
        'peso': 2.0,
        'condicao': lambda v: 1.0 if v > 0.20 else 0.8 if v > 0.15 else 0.4 if v > 0.10 else 0.0
    },
    {
        'nome': 'margem_liquida',
        'cabecalho': 'Check Marg.Líq.',
        'peso': 1.5,
        'condicao': lambda v: 1.0 if v > 0.15 else 0.7 if v > 0.10 else 0.3 if v > 0.05 else 0.0
    },
    {
        'nome': 'div_bruta_patrimonio',
        'cabecalho': 'Check Dív/Patr.',
        'peso': 1.2,
        'condicao': lambda v: 1.0 if v < 0.5 else 0.5 if v < 1.0 else 0.1 if v < 1.5 else 0.0
    },
    {
        'nome': 'liquidez_corrente',
        'cabecalho': 'Check Liq.Corr.',
        'peso': 1.0,
        'condicao': lambda v: 1.0 if v > 2.0 else 0.7 if v > 1.5 else 0.2 if v > 1.0 else 0.0
    },
    {
        'nome': 'psr',
        'cabecalho': 'Check PSR',
        'peso': 0.5,
        'condicao': lambda v: 1.0 if 0 < v <= 1.5 else 0.0
    },
    {
        'nome': 'p_ativo',
        'cabecalho': 'Check P/Ativo',
        'peso': 0.5,
        'condicao': lambda v: 1.0 if 0 < v <= 1.5 else 0.0
    },
    {
        'nome': 'p_cap_giro',
        'cabecalho': 'Check P/Cap.Giro',
        'peso': 0.5,
        'condicao': lambda v: 1.0 if v > 1 else 0.0
    },
    {
        'nome': 'p_ebit',
        'cabecalho': 'Check P/EBIT',
        'peso': 1.0,
        'condicao': lambda v: 1.0 if 0 < v <= 12 else 0.0
    },
    {
        'nome': 'p_ativo_circulante_liq',
        'cabecalho': 'Check P/Ativ.Circ.Liq.',
        'peso': 0.5,
        'condicao': lambda v: 1.0 if 0 < v <= 1.5 else 0.0
    },
    {
        'nome': 'ev_ebitda',
        'cabecalho': 'Check EV/EBITDA',
        'peso': 1.0,
        'condicao': lambda v: 1.0 if 0 < v <= 8 else 0.0
    },
    {
        'nome': 'margem_ebit',
        'cabecalho': 'Check Marg.EBIT',
        'peso': 1.0,
        'condicao': lambda v: 1.0 if v > 0.10 else 0.0
    },
]

# =================================================================
#      ESTRATÉGIAS DE INVESTIMENTO COM PESOS
# =================================================================

ESTRATEGIAS = {
    'graham': {
        'cabecalho': 'Score Graham',
        'peso': 1.0,
        'filtros': ['p_l', 'p_vp', 'liquidez_corrente', 'div_bruta_patrimonio'],
        'descricao': 'Valor + Segurança (Benjamin Graham)'
    },
    'greenblatt': {
        'cabecalho': 'Score Greenblatt',
        'peso': 1.5,
        'filtros': ['roic', 'ev_ebit'],
        'descricao': 'Magic Formula (Joel Greenblatt)'
    },
    'bazin': {
        'cabecalho': 'Score Bazin',
        'peso': 1.0,
        'filtros': ['dividend_yield', 'div_bruta_patrimonio', 'p_l'],
        'descricao': 'Dividendos (Décio Bazin)'
    },
    'qualidade': {
        'cabecalho': 'Score Qualidade',
        'peso': 2.0,
        'filtros': ['roe', 'margem_liquida', 'roic', 'div_bruta_patrimonio'],
        'descricao': 'Qualidade + Rentabilidade'
    }
}

# Soma total de pesos para normalização
SOMA_PESOS_FILTROS = sum(f['peso'] for f in FILTROS)
SOMA_PESOS_ESTRATEGIAS = sum(e['peso'] for e in ESTRATEGIAS.values())
