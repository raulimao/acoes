"""
Script para identificar ativos com setor/subsetor N/A ou vazio
"""
import os
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Buscar todos os ativos da tabela SETORES
data = client.table('setores').select('ativo, setor, subsetor').execute()

print("=" * 80)
print("ATIVOS COM SETOR/SUBSETOR INVÁLIDO (N/A, vazio, None)")
print("=" * 80)

invalid_stocks = []

for stock in data.data:
    setor = stock.get('setor', '')
    subsetor = stock.get('subsetor', '')
    ativo = stock.get('ativo', '')
    
    # Check for invalid values
    setor_invalid = setor is None or str(setor).strip() in ['', 'N/A', 'NA', 'n/a', 'na', 'None', 'null']
    subsetor_invalid = subsetor is None or str(subsetor).strip() in ['', 'N/A', 'NA', 'n/a', 'na', 'None', 'null']
    
    if setor_invalid or subsetor_invalid:
        invalid_stocks.append({
            'ativo': ativo,
            'setor': setor,
            'subsetor': subsetor
        })

print(f"\nTotal de ativos com problemas: {len(invalid_stocks)}")
print("-" * 80)
print(f"{'TICKER':10} | {'SETOR':25} | {'SUBSETOR':25}")
print("-" * 80)

for stock in invalid_stocks[:30]:  # Show top 30
    setor = str(stock['setor']) if stock['setor'] else 'NULL'
    subsetor = str(stock['subsetor']) if stock['subsetor'] else 'NULL'
    print(f"{stock['ativo']:10} | {setor:25} | {subsetor:25}")

print("-" * 80)
print("\nVerifique esses tickers em:")
print("https://www.fundamentus.com.br/detalhes.php?papel=TICKER")
print("(Substitua TICKER pelo código da ação)")
