
import sys
import os
import pandas as pd

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from core.pipeline import carregar_dados_completos

def check_scale():
    print("🔎 Verificando escala dos dados...")
    df = carregar_dados_completos()
    
    if 'dividend_yield' in df.columns:
        print("\nExemplo de Dividend Yield:")
        print(df[['papel', 'dividend_yield', 'red_flags']].head(10))
        
        # Check specific suspect
        if 'EUCA4' in df['papel'].values:
            print("\nEUCA4:")
            print(df[df['papel'] == 'EUCA4'][['papel', 'dividend_yield', 'red_flags']])
            
        print("\nEstatísticas DY:")
        print(df['dividend_yield'].describe())
    else:
        print("Coluna dividend_yield não encontrada")

if __name__ == "__main__":
    check_scale()
