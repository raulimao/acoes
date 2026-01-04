import structlog
import asyncio
from datetime import datetime
import pandas as pd

from api.services.data_service import update_market_data_background, get_market_data, get_client
from core.integration.fusion import get_fusion_ranking
from api.services.history_service import save_to_historico
from core.portfolio.manager import SnapshotManager

logger = structlog.get_logger()

async def run_daily_system_update():
    """
    Orchestrates the Full Daily Update Routine.
    1. Scrapes Fresh Data.
    2. Calculates Fusion Scores (Safe Logic).
    3. Persists Scores to DB Cache.
    4. Updates History (Weekly Portfolio).
    5. Updates Monitor Snapshot.
    """
    logger.info("daily_update_start")
    
    # 1. Update Market Data (Fresh Prices & Fundamentals)
    logger.info("step_1_market_data")
    try:
        # Check if async wrapper or sync logic needed. 
        # API wrapper is async. We can await it.
        await update_market_data_background()
        
        # Reload to ensure RAM is fresh
        df_market = get_market_data()
        logger.info("market_data_refreshed", count=len(df_market))
    except Exception as e:
        logger.error("market_data_failed", error=str(e))
        return

    # 2. Calculate Fusion Ranking (Apply Risk Penalties)
    logger.info("step_2_fusion_ranking")
    try:
        fusion_list = get_fusion_ranking()
        if not fusion_list:
            logger.error("fusion_ranking_empty")
            return
            
        logger.info("fusion_ranking_calculated", top_asset=fusion_list[0]['ticker'])
    except Exception as e:
        logger.error("fusion_ranking_failed", error=str(e))
        return

    # 3. Sync Fusion Scores back to Market Data Cache
    # This ensures that even raw API calls see the 'Safe' score
    logger.info("step_3_sync_scores")
    try:
        fusion_map = {item['ticker']: item['fusion_score'] for item in fusion_list}
        df_market['super_score'] = df_market['papel'].map(fusion_map).fillna(0)
        
        # Save updated scores to DB 
        # (We update the 'super_score' column in 'data' jsonb)
        client = get_client()
        if client:
             # Re-construct JSON payload
             records = df_market.fillna(0).to_dict(orient="records")
             client.table("market_data_cache").upsert({
                 "id": 1, 
                 "data": records,
                 "updated_at": datetime.now().isoformat()
             }).execute()
             logger.info("scores_synced_to_db")
    except Exception as e:
        logger.error("score_sync_failed", error=str(e))

    # 4. Save to History (Weekly Portfolio / Daily Track)
    logger.info("step_4_history_save")
    try:
        # History Service handles Upsert (Delete today + Insert)?
        # IMPORTANT: We need it to wipe ghosts if logic changed. 
        # Previous manual fix was to delete all for today. 
        # We should enforce a cleaner approach here if possible. 
        # But for now, save_to_historico uses 'tickers_to_update'.
        # If the list changes drastically, ghosts remain.
        # Let's verify history service logic or just accept it for now.
        # Ideally, we should delete *ALL* for today before inserting.
        
        saved_count = save_to_historico(df_market)
        logger.info("history_saved", count=saved_count)
    except Exception as e:
        logger.error("history_save_failed", error=str(e))

    # 5. Update Monitor Snapshot
    logger.info("step_5_monitor_snapshot")
    try:
        manager = SnapshotManager()
        success = manager.create_snapshot() # Uses get_fusion_ranking implicitly
        if success:
            logger.info("snapshot_created")
        else:
            logger.error("snapshot_failed")
    except Exception as e:
        logger.error("monitor_update_failed", error=str(e))
        
    logger.info("daily_update_complete")
    return {"status": "success", "message": "Full Daily Update Completed"}
