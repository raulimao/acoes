"""
Script para identificar ativos com problemas de relacionamento entre tabelas
"""
import os
from dotenv import load_dotenv
from supabase import create_client
import pandas as pd

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Buscar todos os setores
setores_data = client.table('setores').select('ativo, setor').execute()
setores_df = pd.DataFrame(setores_data.data)

# Buscar últimos registros do histórico (para pegar todos os ativos ativos)
# Pegando distinct papels do historico recente
historico_data = client.table('historico').select('papel, super_score').order('data', desc=True).limit(500).execute()
historico_df = pd.DataFrame(historico_data.data)
historico_df = historico_df.drop_duplicates(subset=['papel'])

print("=" * 80)
print("VERIFICAÇÃO DE INTEGRIDADE DE DADOS")
print(f"Total de ativos no histórico (amostra): {len(historico_df)}")
print(f"Total de ativos na tabela setores: {len(setores_df)}")
print("=" * 80)

# Merge para ver quem está sem setor
merged = pd.merge(historico_df, setores_df, left_on='papel', right_on='ativo', how='left')

missing_sector = merged[merged['setor'].isna() | (merged['setor'] == '') | (merged['setor'] == 'N/A')]

if len(missing_sector) > 0:
    print("\nATIVOS NO HISTÓRICO SEM CORRESPONDÊNCIA NA TABELA SETORES:")
    print("-" * 80)
    print(f"{'TICKER':10} | {'SCORE':10}")
    print("-" * 80)
    for _, row in missing_sector.iterrows():
        print(f"{row['papel']:10} | {row['super_score']}")
else:
    print("\nTodos os ativos do histórico têm setor correspondente.")

print("\n" + "=" * 80)
