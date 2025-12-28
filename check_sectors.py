
import os
import sys
from dotenv import load_dotenv
import pandas as pd

# Setup path
sys.path.append(os.getcwd())

from services.supabase_client import get_client

def check_missing_sectors():
    load_dotenv()
    client = get_client()
    
    if not client:
        print("Erro: Supabase Client não inicializado.")
        return

    print("Busca dados...")
    
    # 1. Fetch all mapped sectors
    # Note: Fetching all might be okay for < 10k rows
    res_setores = client.table('setores').select('ativo, setor').execute()
    df_setores = pd.DataFrame(res_setores.data)
    
    if df_setores.empty:
        print("Tabela 'setores' vazia.")
        mapped_assets = set()
        na_assets = set()
    else:
        mapped_assets = set(df_setores['ativo'].str.upper().tolist())
        # Assets that exist but have N/A
        na_assets = set(df_setores[df_setores['setor'].isin(['N/A', 'n/a', '', None])]['ativo'].str.upper().tolist())

    # 2. Fetch unique tickers from historico logic
    # Since historico can be huge, we'll try to just fetch distinct 'papel'
    # Supabase-py doesn't support 'distinct' easily on select without .csv() or similar tricks
    # Just fetching 'papel' column - limit 5000 (assuming valid universe is smaller than that)
    try:
        res_hist = client.table('historico').select('papel').order('data', desc=True).limit(2000).execute()
        df_hist = pd.DataFrame(res_hist.data)
        if df_hist.empty:
            print("Tabela 'historico' vazia.")
            history_assets = set()
        else:
            history_assets = set(df_hist['papel'].str.upper().tolist())
            
    except Exception as e:
        print(f"Erro ao buscar historico: {e}")
        return

    # 3. Analysis
    missing_from_mapping = history_assets - mapped_assets
    total_missing = missing_from_mapping.union(na_assets)
    
    with open('missing_sectors.txt', 'w') as f:
        f.write(f"ATIVOS SEM SETOR DEFINIDO ({len(total_missing)})\n")
        f.write("="*50 + "\n")
        
        if len(missing_from_mapping) > 0:
            f.write(f"\n[!] Ausentes na tabela de setores ({len(missing_from_mapping)}):\n")
            f.write(", ".join(sorted(list(missing_from_mapping))) + "\n")
            
        if len(na_assets) > 0:
            f.write(f"\n[!] Mapeados como 'N/A' ({len(na_assets)}):\n")
            f.write(", ".join(sorted(list(na_assets))) + "\n")

    print("Relatório salvo em missing_sectors.txt")

if __name__ == "__main__":
    check_missing_sectors()
