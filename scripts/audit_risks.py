
import sys
import os
import pandas as pd

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from core.pipeline import carregar_dados_completos

def audit():
    print("🔎 Auditando Riscos (Sem persistência)...")
    df = carregar_dados_completos()
    
    if df.empty:
        print("Empty DF")
        return

    print(f"\n✅ Dados Carregados: {len(df)} ações")
    
    if 'red_flags' in df.columns:
        # Count flags
        flagged = df[df['red_flags'].apply(lambda x: len(x) > 0)]
        print(f"🚩 Ações com flags: {len(flagged)}")
        
        print("\nExemplos:")
        print(flagged[['papel', 'red_flags']].head(15).to_string(index=False))
        
        # Check specific flag types
        div_trap = df[df['red_flags'].apply(lambda x: 'DIV_TRAP' in x)]
        print(f"\n⚠️ Dividend Traps (>15% DY): {len(div_trap)}")
        
        debt = df[df['red_flags'].apply(lambda x: 'HIGH_DEBT' in x)]
        print(f"⚠️ Dívida Alta (>3.0x): {len(debt)}")
        
        low_liq = df[df['red_flags'].apply(lambda x: 'LOW_LIQ' in x)]
        print(f"⚠️ Baixa Liquidez (<500k): {len(low_liq)}")
    else:
        print("❌ Coluna red_flags NÃO encontrada!")

if __name__ == "__main__":
    audit()
