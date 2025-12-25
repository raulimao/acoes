"""
Main Data Pipeline
Combines scraping, cleaning, and scoring into a single function
"""
import pandas as pd

from core.fundamentus.scraper import carregar_fundamentus, filtrar_blacklist
from core.fundamentus.cleaner import processar_dados
from core.scoring.calculator import aplicar_scoring_completo, calcular_score_simples


def merge_setores(df: pd.DataFrame) -> pd.DataFrame:
    """
    Merge sector data from Supabase into the DataFrame.
    
    Args:
        df: DataFrame with stock data
        
    Returns:
        DataFrame with setor and subsetor columns
    """
    try:
        from services.setores_service import get_all_setores
        
        df_setores = get_all_setores()
        
        if not df_setores.empty and 'papel' in df.columns:
            # Merge on ticker
            df_setores = df_setores.rename(columns={'ativo': 'papel'})
            df = df.merge(df_setores[['papel', 'setor', 'subsetor']], on='papel', how='left')
            df['setor'] = df['setor'].fillna('N/A')
            df['subsetor'] = df['subsetor'].fillna('N/A')
            print(f"✅ Setores mesclados para {len(df[df['setor'] != 'N/A'])} ações")
        else:
            df['setor'] = 'N/A'
            df['subsetor'] = 'N/A'
            
    except Exception as e:
        print(f"⚠️ Erro ao mesclar setores: {e}")
        df['setor'] = 'N/A'
        df['subsetor'] = 'N/A'
    
    return df


def carregar_dados_completos() -> pd.DataFrame:
    """
    Load, clean, and score all stock data.
    
    Returns:
        DataFrame with all indicators and scores
    """
    try:
        # Step 1: Scrape data
        df = carregar_fundamentus()
        
        # Step 2: Clean data
        df = processar_dados(df)
        
        # Step 3: Filter blacklist
        df = filtrar_blacklist(df)
        
        # Step 4: Apply scoring
        df = aplicar_scoring_completo(df)
        
        # Step 5: Add simple score for backward compatibility
        df["score"] = df.apply(calcular_score_simples, axis=1)
        
        # Step 6: Merge sector data from Supabase
        df = merge_setores(df)
        
        # Step 7: Sort by super_score
        df = df.sort_values("super_score", ascending=False).reset_index(drop=True)
        
        print(f"✅ {len(df)} ações processadas com sucesso!")
        
        return df
        
    except Exception as e:
        print(f"❌ Erro ao processar os dados: {e}")
        return pd.DataFrame()


# Alias for backward compatibility
resultado = carregar_dados_completos
