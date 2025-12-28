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
    
    print("🧹 Limpando e convertendo valores...")
    
    for col in df.columns:
        if col in skip_cols:
            continue
            
        if df[col].dtype == object:
            # Convert to string and strip whitespace
            df[col] = df[col].astype(str).str.strip()
            
            # Replace standalone "-" (meaning null/no value) with empty string
            # BUT preserve negative numbers like "-15.3"
            df[col] = df[col].apply(lambda x: "" if x == "-" else x)
            
            # Replace Brazilian number format (1.234,56 -> 1234.56)
            df[col] = (
                df[col]
                    .str.replace(".", "", regex=False)  # Remove thousand separator
                    .str.replace(",", ".", regex=False)  # Decimal comma to point
                    .str.replace("%", "", regex=False)   # Remove percent sign
            )
            
            # Convert to numeric (preserves negative signs)
            df[col] = pd.to_numeric(df[col], errors="coerce")
    
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
    Filter out stocks with zero liquidity or patrimony.
    
    Args:
        df: DataFrame with stock data
        
    Returns:
        Filtered DataFrame
    """
    if 'liquidez_2meses' in df.columns:
        df = df[df['liquidez_2meses'] > 0]
    
    if 'patrimonio_liquido' in df.columns:
        df = df[df['patrimonio_liquido'] > 0]
    
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
    
    return df
