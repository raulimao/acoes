import os
import pandas as pd
from supabase import create_client
from dotenv import load_dotenv
import matplotlib.pyplot as plt
from api.services.report_service import generate_pdf_report

load_dotenv()

# 1. Fetch Data like API does
def get_real_data():
    client = create_client(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_KEY'))
    
    # Queries from main.py logic (simplified)
    # Assuming get_stock_data basically joins historico and setores
    # But let's fetch raw tables to simulate the join manually if needed, 
    # OR better: inspect the actual data in 'setores' and 'historico' that contributes to the report.
    
    # Fetch latest historico
    hist = client.table('historico').select('*').order('data', desc=True).limit(500).execute()
    df_hist = pd.DataFrame(hist.data)
    df_hist = df_hist.drop_duplicates(subset=['papel'])
    
    # Fetch setores
    setores = client.table('setores').select('*').execute()
    df_setores = pd.DataFrame(setores.data)
    
    # Merge
    df = pd.merge(df_hist, df_setores, left_on='papel', right_on='ativo', how='left')
    
    return df

# 2. Inspect Data
print("Fetching real data...")
df = get_real_data()

print(f"\nTotal records: {len(df)}")

print("\n--- SECTOR ANALYSIS (RAW) ---")
if 'setor' in df.columns:
    unique_sectors = df['setor'].unique()
    print("Unique sectors found:")
    for s in unique_sectors:
        print(f"'{s}' (Type: {type(s)})")
        
    na_sectors = df[df['setor'].isna() | (df['setor'] == 'N/A') | (df['setor'] == '')]
    print(f"\nRecords with N/A sector: {len(na_sectors)}")
    if len(na_sectors) > 0:
        print(na_sectors[['papel', 'setor', 'super_score']].head())

# 3. Generate PDF
print("\nGenerating PDF locally...")
try:
    pdf_bytes = generate_pdf_report(df.copy())
    with open("debug_report.pdf", "wb") as f:
        f.write(pdf_bytes)
    print("SUCCESS: 'debug_report.pdf' created.")
except Exception as e:
    print(f"ERROR generating PDF: {e}")
    import traceback
    traceback.print_exc()

# 4. Verify Layout Pages (Simulated)
# We can't easily count pages of the generated binary here without PyPDF2, 
# but the success functionality of the script confirms the code runs.
