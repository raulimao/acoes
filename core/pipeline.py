"""
Main Data Pipeline
Combines scraping, cleaning, and scoring into a single function
"""
import pandas as pd

from core.fundamentus.scraper import carregar_fundamentus, filtrar_blacklist
from core.fundamentus.cleaner import processar_dados
from core.scoring.calculator import aplicar_scoring_completo, calcular_score_simples



# Legacy merge_setores removed (replaced by merge_details_from_cache)




def merge_details_from_cache(df: pd.DataFrame) -> pd.DataFrame:
    """
    Features Engineering Step:
    Merge detailed data (DRE, Balance Sheet, Oscillations, Setor) from Supabase Cache
    into the DataFrame BEFORE scoring. This allows using deep metrics for strategy calculation.
    """
    try:
        from api.services.supabase_client import get_client
        client = get_client()
        if not client: return df
        
        # Fetch only the 'data' column from cache row id=1
        response = client.table("market_data_cache").select("data").eq("id", 1).maybe_single().execute()
        
        if response.data and response.data.get("data"):
            cache_list = response.data["data"]
            # Convert to Dictionary {ticker: record} for fast lookup
            cache_map = {item.get('papel'): item for item in cache_list if item.get('papel')}
            
            print(f"🔄 Mesclando detalhes de {len(cache_map)} ativos do cache...")
            
            # Smart Merge: 
            # We want to keep FRESh prices from Scraper (df), but add DETAILS from Cache (cache_map)
            # If a column exists in both, Scraper (df) priority? 
            # Actually, Scraper is "Simple", Cache has "Details".
            
            # Create list of dicts from current DF
            current_records = df.to_dict(orient="records")
            merged_records = []
            
            for item in current_records:
                ticker = item.get('papel')
                if ticker in cache_map:
                    cached = cache_map[ticker]
                    # Merge cached into item, but keep fresh values if they exist in item
                    # So: start with CACHED (base), update with FRESH (overlay)
                    # This ensures we get DRE/Setor not in Fresh, but Fresh Price overwrites Cached Price
                    
                    # BUT: item keys are normalized (p_l), cached keys might include raw?
                    # Cache already comes from data_service which has merged normalization.
                    
                    final_item = cached.copy()
                    final_item.update(item) # Valid Fresh data overwrites Old Cache
                    
                    # Normalize keys to match cleaner.py format (lowercase + snake_case)
                    # Use a fast list comp or dict comp
                    normalized_item = {}
                    for k, v in final_item.items():
                         # Simple normalization: lower() and replace special chars if needed
                         # But cleaner.py uses regex. Let's try to match basic expectation (lower)
                         # Setor -> setor, Subsetor -> subsetor, dre_12m... -> dre_12m...
                         clean_k = k.lower().replace(" ", "_").replace(".", "")
                         normalized_item[clean_k] = v
                    
                    merged_records.append(normalized_item)
                else:
                    merged_records.append(item)
            
            return pd.DataFrame(merged_records)
            
    except Exception as e:
        print(f"⚠️ Erro ao mesclar detalhes do cache: {e}")
        
    return df

def carregar_dados_completos() -> pd.DataFrame:
    """
    Load, clean, and score all stock data.
    """
    try:
        # Step 1: Scrape data (Simple Table from Web)
        df = carregar_fundamentus()
        
        # Step 2: Clean data
        df = processar_dados(df)
        
        # Step 3: Filter blacklist
        df = filtrar_blacklist(df)
        
        # Step 4: Merge DETAILS from Cache (DRE, Setor, Oscilacoes, Balanco)
        # CRITICAL FIX: Merge BEFORE scoring to allow using deep metrics
        df = merge_details_from_cache(df)
        
        # Step 5: Apply scoring (Now has access to Sector, Margins, Debt)
        df = aplicar_scoring_completo(df)
        
        # Step 6: Add simple score for backward compatibility
        df["score"] = df.apply(calcular_score_simples, axis=1)
        
        # Step 7 (Optional): Legacy Sector Merge (kept for safety, maybe redundant now)
        # df = merge_setores(df) 
        # (merge_details_from_cache already does this if cache is populated)
        
        # Step 8: Sort by super_score
        df = df.sort_values("super_score", ascending=False).reset_index(drop=True)
        
        print(f"✅ {len(df)} ações processadas com sucesso!")
        
        return df
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"❌ Erro ao processar os dados: {e}")
        return pd.DataFrame()


# Alias for backward compatibility
resultado = carregar_dados_completos
