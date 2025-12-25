"""
History Service using Supabase
Handles saving and retrieving stock history data
"""
import pandas as pd
from datetime import datetime, date
from typing import List, Optional

from services.supabase_client import get_client, is_configured
from config.settings import SCORE_MINIMO_HISTORICO, COLUNAS_HISTORICO


def save_to_historico(df: pd.DataFrame, score_minimo: float = None) -> int:
    """
    Save qualified stocks to history table.
    
    Args:
        df: DataFrame with stock data including super_score
        score_minimo: Minimum super_score to qualify (default from settings)
        
    Returns:
        Number of records saved
    """
    if not is_configured():
        print("⚠️ Supabase não configurado. Histórico não será salvo.")
        return 0
    
    client = get_client()
    if not client:
        return 0
    
    if score_minimo is None:
        score_minimo = SCORE_MINIMO_HISTORICO
    
    # Filter stocks with score above minimum
    df_qualified = df[df['super_score'] >= score_minimo].copy()
    
    if df_qualified.empty:
        print(f"ℹ️ Nenhuma ação com Super Score >= {score_minimo}")
        return 0
    
    # Prepare data for insertion
    today = datetime.now().isoformat()
    records = []
    
    for _, row in df_qualified.iterrows():
        record = {
            'data': today,
            'papel': row.get('papel', ''),
            'cotacao': float(row.get('cotacao', 0)) if pd.notna(row.get('cotacao')) else None,
            'p_l': float(row.get('p_l', 0)) if pd.notna(row.get('p_l')) else None,
            'p_vp': float(row.get('p_vp', 0)) if pd.notna(row.get('p_vp')) else None,
            'dividend_yield': float(row.get('dividend_yield', 0)) if pd.notna(row.get('dividend_yield')) else None,
            'roe': float(row.get('roe', 0)) if pd.notna(row.get('roe')) else None,
            'roic': float(row.get('roic', 0)) if pd.notna(row.get('roic')) else None,
            'score_graham': float(row.get('score_graham', 0)) if pd.notna(row.get('score_graham')) else None,
            'score_greenblatt': float(row.get('score_greenblatt', 0)) if pd.notna(row.get('score_greenblatt')) else None,
            'score_bazin': float(row.get('score_bazin', 0)) if pd.notna(row.get('score_bazin')) else None,
            'score_qualidade': float(row.get('score_qualidade', 0)) if pd.notna(row.get('score_qualidade')) else None,
            'super_score': float(row.get('super_score', 0)) if pd.notna(row.get('super_score')) else None,
        }
        records.append(record)
    
    try:
        # Insert records
        result = client.table('historico').insert(records).execute()
        saved_count = len(result.data) if result.data else 0
        print(f"✅ {saved_count} ações salvas no histórico")
        return saved_count
    except Exception as e:
        print(f"❌ Erro ao salvar histórico: {e}")
        return 0


def get_historico(dias: int = 30, papel: str = None) -> pd.DataFrame:
    """
    Retrieve history data from Supabase with pagination to get all records.
    
    Args:
        dias: Number of days to look back
        papel: Optional filter by stock ticker
        
    Returns:
        DataFrame with history data
    """
    if not is_configured():
        return pd.DataFrame()
    
    client = get_client()
    if not client:
        return pd.DataFrame()
    
    try:
        from_date = (datetime.now() - pd.Timedelta(days=dias)).isoformat()
        
        all_data = []
        page_size = 1000
        offset = 0
        
        while True:
            query = client.table('historico').select('*')
            query = query.gte('data', from_date)
            
            if papel:
                query = query.eq('papel', papel)
            
            # Paginate with range
            query = query.order('data', desc=True).range(offset, offset + page_size - 1)
            result = query.execute()
            
            if not result.data:
                break
                
            all_data.extend(result.data)
            
            # If we got less than page_size, we've reached the end
            if len(result.data) < page_size:
                break
                
            offset += page_size
        
        if all_data:
            return pd.DataFrame(all_data)
        return pd.DataFrame()
        
    except Exception as e:
        print(f"❌ Erro ao buscar histórico: {e}")
        return pd.DataFrame()


def remove_duplicates_same_day() -> int:
    """
    Remove duplicate entries for the same stock on the same day.
    Keeps only the most recent entry.
    
    Returns:
        Number of duplicates removed
    """
    if not is_configured():
        return 0
    
    client = get_client()
    if not client:
        return 0
    
    try:
        # Get today's date
        today = date.today().isoformat()
        
        # Get all entries for today
        result = client.table('historico').select('id, papel, data').gte('data', today).execute()
        
        if not result.data:
            return 0
        
        # Find duplicates (same papel on same day)
        df = pd.DataFrame(result.data)
        df['date_only'] = pd.to_datetime(df['data']).dt.date
        
        # Group by papel and date, keep only first (most recent)
        duplicates = df.groupby(['papel', 'date_only']).apply(
            lambda x: x.iloc[1:]['id'].tolist() if len(x) > 1 else []
        ).explode().dropna().tolist()
        
        # Delete duplicates
        if duplicates:
            for id_to_delete in duplicates:
                client.table('historico').delete().eq('id', id_to_delete).execute()
            print(f"🗑️ {len(duplicates)} duplicatas removidas")
            return len(duplicates)
        
        return 0
        
    except Exception as e:
        print(f"❌ Erro ao remover duplicatas: {e}")
        return 0
