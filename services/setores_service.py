"""
Setores Service using Supabase
Handles caching and retrieving sector data
"""
import pandas as pd
from typing import Optional, Dict

from services.supabase_client import get_client, is_configured


def get_setor_from_cache(ticker: str) -> Optional[Dict[str, str]]:
    """
    Get sector info from Supabase cache.
    
    Args:
        ticker: Stock ticker symbol
        
    Returns:
        Dict with 'setor' and 'subsetor' or None if not found
    """
    if not is_configured():
        return None
    
    client = get_client()
    if not client:
        return None
    
    try:
        result = client.table('setores').select('setor, subsetor').eq('ativo', ticker).execute()
        
        if result.data and len(result.data) > 0:
            return {
                'setor': result.data[0].get('setor', 'N/A'),
                'subsetor': result.data[0].get('subsetor', 'N/A')
            }
        return None
        
    except Exception as e:
        print(f"⚠️ Erro ao buscar setor de {ticker}: {e}")
        return None


def save_setor_to_cache(ticker: str, setor: str, subsetor: str) -> bool:
    """
    Save sector info to Supabase cache.
    
    Args:
        ticker: Stock ticker symbol
        setor: Sector name
        subsetor: Subsector name
        
    Returns:
        True if saved successfully
    """
    if not is_configured():
        return False
    
    client = get_client()
    if not client:
        return False
    
    try:
        # Upsert (insert or update)
        result = client.table('setores').upsert({
            'ativo': ticker,
            'setor': setor,
            'subsetor': subsetor
        }, on_conflict='ativo').execute()
        
        return bool(result.data)
        
    except Exception as e:
        print(f"⚠️ Erro ao salvar setor de {ticker}: {e}")
        return False


def get_all_setores() -> pd.DataFrame:
    """
    Get all sectors from Supabase cache.
    
    Returns:
        DataFrame with all sector data
    """
    if not is_configured():
        return pd.DataFrame()
    
    client = get_client()
    if not client:
        return pd.DataFrame()
    
    try:
        result = client.table('setores').select('*').execute()
        
        if result.data:
            return pd.DataFrame(result.data)
        return pd.DataFrame()
        
    except Exception as e:
        print(f"❌ Erro ao buscar setores: {e}")
        return pd.DataFrame()


def import_setores_from_excel(excel_path: str) -> int:
    """
    Import sectors from Excel file to Supabase.
    
    Args:
        excel_path: Path to Excel file with 'Setores' sheet
        
    Returns:
        Number of sectors imported
    """
    if not is_configured():
        print("⚠️ Supabase não configurado")
        return 0
    
    client = get_client()
    if not client:
        return 0
    
    try:
        # Read Excel
        df = pd.read_excel(excel_path, sheet_name='Setores')
        
        if df.empty:
            print("ℹ️ Nenhum setor encontrado no Excel")
            return 0
        
        # Prepare records
        records = []
        for _, row in df.iterrows():
            record = {
                'ativo': str(row.get('Ativo', '')),
                'setor': str(row.get('Setor', 'N/A')),
                'subsetor': str(row.get('Subsetor', 'N/A'))
            }
            if record['ativo']:
                records.append(record)
        
        # Batch upsert
        if records:
            result = client.table('setores').upsert(records, on_conflict='ativo').execute()
            count = len(result.data) if result.data else 0
            print(f"✅ {count} setores importados do Excel")
            return count
        
        return 0
        
    except Exception as e:
        print(f"❌ Erro ao importar setores: {e}")
        return 0
