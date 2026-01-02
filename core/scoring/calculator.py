"""
Scoring Calculator
Implements gradual scoring with weights and investment strategies
"""
import pandas as pd
import numpy as np
from typing import Dict, List

from config.strategies_config import FILTROS, ESTRATEGIAS


def check_red_flags(row: pd.Series) -> List[str]:
    """Identifies potential risks in the asset."""
    flags = []
    
    # 1. Dividend Trap (Too high)
    dy = row.get('dividend_yield', 0)
    if dy > 0.15: # > 15%
        flags.append('DIV_TRAP')
        
    # 2. Margin Collapse (Too low)
    margem = row.get('margem_liquida', 0)
    if 0 < margem < 0.03: # < 3%
        flags.append('LOW_MARGIN')
        
    # 3. High Debt
    div_pat = row.get('div_bruta_patrimonio', 0)
    if div_pat > 3.0:
        flags.append('HIGH_DEBT')
        
    # 4. Low Liquidity
    liq = row.get('liquidez_2meses', 0)
    if liq < 500_000:
        flags.append('LOW_LIQ')
    
    # ====== NEW FLAGS (Sprint 1) ======
    
    # 5. Stagnant Company (Negative Growth)
    growth = row.get('crescimento_receita_5a', 0)
    if growth < 0:  # Revenue shrinking over 5 years
        flags.append('STAGNANT')
    
    # 6. Cyclical Sector Warning
    setor = str(row.get('setor', '')).lower()
    cyclical_keywords = ['mineração', 'mineracao', 'petróleo', 'petroleo', 
                         'siderurgia', 'metalurgia', 'papel', 'celulose', 'commodities']
    if any(kw in setor for kw in cyclical_keywords):
        flags.append('CYCLICAL')
    
    # 7. High Regulatory Risk Sector
    regulated_keywords = ['energia', 'elétrica', 'eletrica', 'saúde', 'saude', 
                          'educação', 'educacao', 'telecom', 'saneamento', 'água', 'agua']
    if any(kw in setor for kw in regulated_keywords):
        flags.append('REGULATED')
        
    return flags

def calcular_score_filtro(valor: float, filtro: dict) -> float:
    """
    Calculate gradual score for a single filter.
    
    Args:
        valor: The indicator value
        filtro: Filter configuration with 'condicao' lambda
        
    Returns:
        Score between 0.0 and 1.0 multiplied by weight
    """
    if pd.isna(valor):
        return 0.0
    
    try:
        score_gradual = filtro['condicao'](valor)
        peso = filtro.get('peso', 1.0)
        return score_gradual * peso
    except Exception:
        return 0.0


def calcular_scores_filtros(row: pd.Series) -> Dict[str, float]:
    """
    Calculate scores for all individual filters.
    
    Args:
        row: DataFrame row with stock data
        
    Returns:
        Dictionary with filter scores
    """
    scores = {}
    
    for filtro in FILTROS:
        nome = filtro['nome']
        valor = row.get(nome, 0)
        scores[nome] = calcular_score_filtro(valor, filtro)
    
    return scores


def calcular_score_estrategia(scores_filtros: Dict[str, float], estrategia: dict) -> float:
    """
    Calculate score for a specific investment strategy.
    
    Args:
        scores_filtros: Dictionary with individual filter scores
        estrategia: Strategy configuration
        
    Returns:
        Strategy score
    """
    score = 0.0
    
    for nome_filtro in estrategia['filtros']:
        if nome_filtro in scores_filtros:
            score += scores_filtros[nome_filtro]
    
    return score


def calcular_super_score(scores_estrategias: Dict[str, float]) -> float:
    """
    Calculate Super Score combining all strategies with weights.
    
    Args:
        scores_estrategias: Dictionary with strategy scores
        
    Returns:
        Super Score
    """
    super_score = 0.0
    
    for nome, config in ESTRATEGIAS.items():
        if nome in scores_estrategias:
            peso = config.get('peso', 1.0)
            super_score += scores_estrategias[nome] * peso
    
    return round(super_score, 2)


def aplicar_scoring_completo(df: pd.DataFrame) -> pd.DataFrame:
    """
    Apply complete scoring system to DataFrame.
    Adds columns for each strategy score and Super Score.
    
    Args:
        df: DataFrame with cleaned stock data
        
    Returns:
        DataFrame with all score columns added
    """
    print("📊 Calculando scores de estratégias...")
    
    # Initialize score columns
    for nome in ESTRATEGIAS.keys():
        df[f'score_{nome}'] = 0.0
    df['super_score'] = 0.0
    df['red_flags'] = [[] for _ in range(len(df))] # Initialize list column
    
    # Calculate scores for each row
    for idx, row in df.iterrows():
        # Check Red Flags
        flags = check_red_flags(row)
        df.at[idx, 'red_flags'] = flags
        
        # Calculate individual filter scores
        scores_filtros = calcular_scores_filtros(row)
        
        # Calculate strategy scores
        scores_estrategias = {}
        for nome, config in ESTRATEGIAS.items():
            scores_estrategias[nome] = calcular_score_estrategia(scores_filtros, config)
            df.at[idx, f'score_{nome}'] = round(scores_estrategias[nome], 2)
        
        # Calculate Super Score
        super_score = calcular_super_score(scores_estrategias)
        
        # Apply Liquidity Penalty (Kill Switch)
        if 'LOW_LIQ' in flags:
            super_score = min(super_score, 50.0)
            
        df.at[idx, 'super_score'] = super_score
    
    return df


def calcular_score_simples(row: pd.Series) -> float:
    """
    Calculate simple score (legacy method for backward compatibility).
    
    Args:
        row: DataFrame row with stock data
        
    Returns:
        Simple score 0-100
    """
    criterios = {
        "p_l": ("<", 15),
        "p_vp": ("<=", 1.5),
        "psr": ("<=", 1.5),
        "dividend_yield": (">", 4),
        "p_ativo": ("<=", 1.5),
        "p_cap_giro": (">=", 1),
        "p_ebit": ("<", 12),
        "p_ativo_circulante_liq": ("<", 1.5),
        "ev_ebit": ("<", 10),
        "ev_ebitda": ("<", 8),
        "margem_ebit": (">=", 10),
        "margem_liquida": (">=", 5),
        "liquidez_corrente": (">=", 1.5),
        "roic": (">", 10),
        "roe": (">", 15),
        "div_bruta_patrimonio": ("<", 0.5),
    }
    
    total = len(criterios)
    pontos = 0
    
    for indicador, (op, ideal) in criterios.items():
        valor = row.get(indicador)
        if pd.isna(valor):
            continue
        if op in ("<", "<="):
            if valor > 0:
                pontos += min(1, ideal / valor)
        else:
            pontos += min(1, valor / ideal)
    
    return round((pontos / total) * 100, 2)
