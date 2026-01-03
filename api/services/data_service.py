
import pandas as pd
from datetime import datetime
import asyncio
from api.services.supabase_client import get_client
from core.pipeline import carregar_dados_completos
import structlog
import os

logger = structlog.get_logger()

# Global RAM cache (Singleton)
_ram_cache = None
_last_update = None

def get_market_data() -> pd.DataFrame:
    """
    Get stock data with multi-layer caching strategy:
    1. RAM (Fastest)
    2. Supabase Cache (Fast persistence)
    3. Scraper (Slow fallback)
    """
    global _ram_cache, _last_update
    
    # 1. Try RAM
    if _ram_cache is not None and not _ram_cache.empty:
        return _ram_cache
        
    logger.info("cache_miss_ram")
    
    # 2. Try Supabase
    try:
        client = get_client()
        if client:
            response = client.table("market_data_cache").select("data, updated_at").eq("id", 1).maybe_single().execute()
            
            if response.data and response.data.get("data"):
                data_list = response.data["data"]
                if data_list:
                    df = pd.DataFrame(data_list)
                    
                    # Validate Schema - Force refresh if new columns missing
                    if 'red_flags' not in df.columns:
                        logger.warning("cache_db_outdated_missing_flags")
                        raise Exception("Cache Schema Mismatch: Missing red_flags")
                    
                    logger.info("cache_hit_db", rows=len(data_list), age=response.data.get("updated_at"))
                    
                    # Update RAM
                    _ram_cache = df
                    _last_update = datetime.now()
                    return df
    except Exception as e:
        logger.error("cache_db_read_failed", error=str(e))

    # 3. Fallback: Run Scraper Sync (Only if DB is empty/unreachable)
    logger.warning("cache_miss_db_running_scraper")
    success = run_scraper_update_sync()
    
    if success and _ram_cache is not None:
        return _ram_cache
        
    return pd.DataFrame()

def run_scraper_update_sync() -> bool:
    """Run scraper synchronously and update both DB and RAM."""
    global _ram_cache, _last_update
    
    try:
        logger.info("scraper_start")
        df = carregar_dados_completos()
        
        if df.empty:
            logger.error("scraper_returned_empty")
            return False
            
        # Update RAM immediately
        _ram_cache = df
        _last_update = datetime.now()
        
        # Save to DB (Best effort)
        # Save to DB (Best effort) with Smart Merge
        try:
            client = get_client()
            if client:
                # 1. Fetch existing data to preserve extra columns (DRE, Balaço, etc)
                existing_response = client.table("market_data_cache").select("data").eq("id", 1).maybe_single().execute()
                existing_map = {}
                
                if existing_response.data and existing_response.data.get("data"):
                    # Create map {ticker: record}
                    for item in existing_response.data["data"]:
                        if 'papel' in item:
                            existing_map[item['papel']] = item
                
                # 2. Prepare new data
                new_records = df.fillna(0).to_dict(orient="records")
                merged_data = []
                
                for new_item in new_records:
                    ticker = new_item.get('papel')
                    if ticker and ticker in existing_map:
                        # Smart Merge: Start with existing (details) -> Update with New (prices/scores)
                        # This preserves 'dre_...', 'oscilacao_...' while updating 'cotacao', 'p_l', 'super_score'
                        merged_item = existing_map[ticker].copy()
                        merged_item.update(new_item)
                        merged_data.append(merged_item)
                    else:
                        merged_data.append(new_item)
                
                # 3. Upsert Merged Data
                client.table("market_data_cache").upsert({
                    "id": 1,
                    "data": merged_data,
                    "updated_at": datetime.now().isoformat()
                }).execute()
                
                logger.info("db_cache_updated_merged", count=len(merged_data))
        except Exception as db_err:
            logger.error("db_cache_write_failed", error=str(db_err))
            
        return True
        
    except Exception as e:
        logger.error("scraper_failed", error=str(e))
        return False

async def update_market_data_background():
    """Async wrapper/background task for scraper update."""
    logger.info("background_update_triggered")
    # Run sync function in thread pool to avoid blocking async loop
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(None, run_scraper_update_sync)
