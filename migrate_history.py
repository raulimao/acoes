"""
Migration Script: Import historical data from Acoes.xlsx to Supabase
Migrates the 'Historico' sheet (June-September 2025) to the Supabase historico table
"""
import pandas as pd
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from services.supabase_client import get_client, is_configured


def migrate_excel_history():
    """Migrate historical data from Excel to Supabase."""
    
    if not is_configured():
        print("❌ Supabase não configurado. Configure as variáveis de ambiente.")
        return 0
    
    client = get_client()
    if not client:
        print("❌ Não foi possível conectar ao Supabase.")
        return 0
    
    # Read Excel file
    print("📚 Lendo arquivo Acoes.xlsx...")
    try:
        df = pd.read_excel('Acoes.xlsx', sheet_name='Historico')
        print(f"   Encontrados {len(df)} registros")
    except Exception as e:
        print(f"❌ Erro ao ler Excel: {e}")
        return 0
    
    # Column mapping from Excel to Supabase
    column_mapping = {
        'Data': 'data',
        'Ativos': 'papel',
        'Cotação': 'cotacao',
        'P/L': 'p_l',
        'P/VP': 'p_vp',
        'Dividend Yield': 'dividend_yield',
        'ROE': 'roe',
        'ROIC': 'roic',
        'Score Graham': 'score_graham',
        'Score Greenblatt': 'score_greenblatt',
        'Score Bazin': 'score_bazin',
        'Score Qualidade': 'score_qualidade',
        'Super Score': 'super_score'
    }
    
    # Rename columns
    df_renamed = df.rename(columns=column_mapping)
    
    # Select only needed columns
    needed_columns = list(column_mapping.values())
    df_clean = df_renamed[[col for col in needed_columns if col in df_renamed.columns]].copy()
    
    # Convert data to ISO format string
    df_clean['data'] = pd.to_datetime(df_clean['data']).dt.strftime('%Y-%m-%dT%H:%M:%S')
    
    # Replace NaN with None for JSON serialization
    df_clean = df_clean.where(pd.notna(df_clean), None)
    
    # Convert to records
    records = df_clean.to_dict(orient='records')
    
    # Clean up None values in records
    for record in records:
        for key, value in record.items():
            if pd.isna(value) if isinstance(value, float) else False:
                record[key] = None
    
    print(f"📤 Enviando {len(records)} registros para Supabase...")
    
    # Insert in batches of 500
    batch_size = 500
    total_inserted = 0
    
    for i in range(0, len(records), batch_size):
        batch = records[i:i + batch_size]
        try:
            result = client.table('historico').insert(batch).execute()
            inserted = len(result.data) if result.data else 0
            total_inserted += inserted
            print(f"   ✅ Lote {i//batch_size + 1}: {inserted} registros inseridos")
        except Exception as e:
            print(f"   ❌ Erro no lote {i//batch_size + 1}: {e}")
            # Continue with next batch
            continue
    
    print(f"\n🎉 Migração concluída! {total_inserted} de {len(records)} registros importados.")
    return total_inserted


if __name__ == "__main__":
    migrate_excel_history()
