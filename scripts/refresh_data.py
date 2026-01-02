
import sys
import os
import pandas as pd
from datetime import datetime

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.pipeline import carregar_dados_completos
from api.services.supabase_client import get_client

def refresh_data():
    print("🚀 Iniciando atualização de dados com Detecção de Riscos...")
    
    # 1. Pipeline Completo (Scraping + Scoring + Flags)
    df = carregar_dados_completos()
    
    if df.empty:
        print("❌ Erro: Pipeline retornou DataFrame vazio.")
        return
    
    # 2. Análise de Flags
    if 'red_flags' in df.columns:
        total_flags = df['red_flags'].apply(lambda x: len(x) if isinstance(x, list) else 0).sum()
        flagged_stocks = df[df['red_flags'].apply(lambda x: len(x) > 0 if isinstance(x, list) else False)]
        
        print(f"\n📊 Análise de Riscos:")
        print(f"   • Total de Ações: {len(df)}")
        print(f"   • Total de Flags Geradas: {total_flags}")
        print(f"   • Ações com Alertas: {len(flagged_stocks)}")
        
        print("\n🚩 Top 5 Ações Mais Arriscadas:")
        for _, row in flagged_stocks.head(5).iterrows():
            print(f"   - {row['papel']}: {row['red_flags']}")
    else:
        print("⚠️ Coluna 'red_flags' não encontrada no DataFrame!")
        
    # 3. Salvar no Supabase
    client = get_client()
    if client:
        print("\n💾 Salvando no Supabase...")
        try:
            # Convert to dict
            data = df.fillna(0).to_dict(orient="records")
            
            client.table("market_data_cache").upsert({
                "id": 1,
                "data": data,
                "updated_at": datetime.now().isoformat()
            }).execute()
            print("✅ Banco de Dados Atualizado com Sucesso!")
        except Exception as e:
            print(f"❌ Erro ao salvar no Supabase: {e}")
    else:
        print("⚠️ Supabase não configurado/conectado. Dados não foram salvos.")

if __name__ == "__main__":
    refresh_data()
