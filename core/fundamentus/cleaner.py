"""
Data Cleaner for Fundamentus Data
Handles column renaming and value normalization
"""
import pandas as pd
import numpy as np


# Column name mapping (original -> normalized)
COLUMN_MAPPING = {
    "Papel": "papel",
    "Cotação": "cotacao",
    "P/L": "p_l",
    "P/VP": "p_vp",
    "PSR": "psr",
    "Div.Yield": "dividend_yield",
    "P/Ativo": "p_ativo",
    "P/Cap.Giro": "p_cap_giro",
    "P/EBIT": "p_ebit",
    "P/Ativ Circ.Liq": "p_ativo_circulante_liq",
    "EV/EBIT": "ev_ebit",
    "EV/EBITDA": "ev_ebitda",
    "Mrg Ebit": "margem_ebit",
    "Mrg. Líq.": "margem_liquida",
    "Liq. Corr.": "liquidez_corrente",
    "ROIC": "roic",
    "ROE": "roe",
    "Liq.2meses": "liquidez_2meses",
    "Patrim. Líq": "patrimonio_liquido",
    "Dív.Brut/ Patrim.": "div_bruta_patrimonio",
    "Cresc. Rec.5a": "crescimento_receita_5a"
}


def renomear_colunas(df: pd.DataFrame) -> pd.DataFrame:
    """
    Rename columns from Portuguese to normalized names.
    
    Args:
        df: Raw DataFrame from Fundamentus
        
    Returns:
        DataFrame with normalized column names
    """
    df = df.rename(columns=COLUMN_MAPPING)
    df.columns = df.columns.str.lower().str.replace(r"[^\w]+", "_", regex=True)
    return df



def clean_value(x):
    """
    Clean and convert value to float.
    Handles percentages, currency formatting, and NaN.
    IMPORTANT: If already numeric, return as-is to avoid double-conversion.
    """
    if pd.isna(x):
        return 0.0
    
    # If already a numeric type (float/int), return as-is
    if isinstance(x, (int, float, np.integer, np.floating)):
        return float(x)
    
    s = str(x).strip()
    
    if s in ["-", "N/A", ""]:
        return 0.0
        
    try:
        # Remove % and convert
        is_pct = "%" in s
        s = s.replace("%", "").replace(".", "").replace(",", ".")
        val = float(s)
        
        if is_pct:
            val /= 100
            
        return val
    except ValueError:
        return 0.0


def limpar_valores(df: pd.DataFrame, skip_cols: list = None) -> pd.DataFrame:
    """
    Clean and convert string values to numeric.
    
    Args:
        df: DataFrame with string values
        skip_cols: Columns to skip (default: ['papel'])
        
    Returns:
        DataFrame with numeric values
    """
    if skip_cols is None:
        skip_cols = ["papel"]
    
    print("🧹 Limpando e convertendo valores (v2 - Unified)...")
    
    for col in df.columns:
        if col in skip_cols:
            continue
            
        # Apply local cleaner
        df[col] = df[col].apply(clean_value)
            
    return df



def corrigir_p_ativo_e_psr(df: pd.DataFrame) -> pd.DataFrame:
    """
    Fix P/Ativo and PSR values that may be scaled incorrectly.
    
    Args:
        df: DataFrame with stock data
        
    Returns:
        Corrected DataFrame
    """
    for col in ["p_ativo", "psr"]:
        if col in df.columns:
            df[col] = df[col].apply(
                lambda x: x / 1000 if pd.notna(x) and x > 100 else x
            )
    return df


def corrigir_cotacoes(df: pd.DataFrame) -> pd.DataFrame:
    """
    Fix stock prices that may be scaled incorrectly.
    
    Args:
        df: DataFrame with stock data
        
    Returns:
        Corrected DataFrame
    """
    def ajustar(x):
        if pd.isna(x):
            return x
        if x > 1000 or (x > 100 and x % 1 == 0):
            return x / 100
        return x
    
    if 'cotacao' in df.columns:
        df["cotacao"] = df["cotacao"].apply(ajustar)
    
    return df


def filtrar_liquidez(df: pd.DataFrame) -> pd.DataFrame:
    """
    Filter out stocks with zero liquidity.
    Note: We do NOT filter patrimonio_liquido anymore to capture 
    companies with negative equity for complete analysis.
    
    Args:
        df: DataFrame with stock data
        
    Returns:
        Filtered DataFrame
    """
    if 'liquidez_2meses' in df.columns:
        df = df[df['liquidez_2meses'] > 0]
    
    # NOTE: Removed patrimonio_liquido > 0 filter to capture all data
    # including companies with negative equity (P/VP, Div/Pat etc will be negative)
    
    return df


def deduplicar_classes(df: pd.DataFrame) -> pd.DataFrame:
    """
    Remove duplicate stock classes (e.g., SOND3, SOND5, SOND6).
    Keeps only the most liquid ticker for each company.
    
    Logic:
    - Extract base ticker (first 4 chars: SOND from SOND3)
    - Group by base ticker
    - Keep only the row with highest liquidez_2meses
    
    Args:
        df: DataFrame with stock data
        
    Returns:
        DataFrame with unique companies (most liquid class only)
    """
    if 'papel' not in df.columns or 'liquidez_2meses' not in df.columns:
        return df
    
    # Extract base ticker (first 4 characters)
    df['base_ticker'] = df['papel'].str[:4]
    
    # Sort by liquidity descending, then keep first (most liquid)
    df = df.sort_values('liquidez_2meses', ascending=False)
    df = df.drop_duplicates(subset='base_ticker', keep='first')
    
    # Remove helper column
    df = df.drop(columns=['base_ticker'])
    
    print(f"🔄 Deduplicação: {len(df)} ativos únicos após remover classes duplicadas")
    
    return df


def processar_dados(df: pd.DataFrame) -> pd.DataFrame:
    """
    Full data processing pipeline.
    
    Args:
        df: Raw DataFrame from Fundamentus
        
    Returns:
        Cleaned and processed DataFrame
    """
    df = renomear_colunas(df)
    df = limpar_valores(df)
    df = corrigir_p_ativo_e_psr(df)
    df = corrigir_cotacoes(df)
    df = filtrar_liquidez(df)
    df = deduplicar_classes(df)  # NEW: Remove duplicate stock classes
    
    return df
