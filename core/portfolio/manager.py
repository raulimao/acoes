
"""
Portfolio Snapshot Manager
Handles creation, retrieval, and comparison of weekly portfolio snapshots.
"""
import pandas as pd
from datetime import datetime
import json
import structlog
from typing import Dict, List, Optional
from api.services.supabase_client import get_client
from api.services.data_service import get_market_data

logger = structlog.get_logger()

class SnapshotManager:
    def __init__(self):
        self.client = get_client()

    def create_snapshot(self, snapshot_date: str = None) -> bool:
        """
        Captures the current market state and saves it as a frozen snapshot.
        """
        if not snapshot_date:
            snapshot_date = datetime.now().strftime('%Y-%m-%d')
            
        logger.info("snapshot_creation_start", date=snapshot_date)
        
        # 1. Get Fusion Ranking Data (Ações Perfeitas)
        from core.integration.fusion import get_fusion_ranking
        fusion_data = get_fusion_ranking()
        
        if not fusion_data:
            logger.error("snapshot_failed_empty_fusion_data")
            return False

        # 2. Serialize Data
        # Fusion returns a list of dicts, so we can use it directly
        assets_list = fusion_data
        
        # 3. Prepare Payload
        payload = {
            "snapshot_date": snapshot_date,
            "assets": assets_list,
            "metadata": {
                "total_assets": len(assets_list),
                "algorithm_version": "2.0",
                "created_by": "automation"
            }
        }
        
        # 4. Save to Supabase
        try:
            # Check if exists (upsert logic if needed, but uniqueness constraint handles it)
            # Using upsert
            self.client.table("portfolio_snapshots").upsert(payload, on_conflict="snapshot_date").execute()
            logger.info("snapshot_creation_success", count=len(assets_list))
            return True
            
        except Exception as e:
            logger.error("snapshot_creation_error", error=str(e))
            return False

    def get_latest_snapshot(self) -> Optional[Dict]:
        """Retrieve the most recent snapshot."""
        try:
            response = self.client.table("portfolio_snapshots") \
                .select("*") \
                .order("snapshot_date", desc=True) \
                .limit(1) \
                .maybe_single() \
                .execute()
                
            return response.data
        except Exception as e:
            logger.error("snapshot_fetch_error", error=str(e))
            return None

    def get_snapshot_by_date(self, date_str: str) -> Optional[Dict]:
        """Retrieve a snapshot for a specific date."""
        try:
            response = self.client.table("portfolio_snapshots") \
                .select("*") \
                .eq("snapshot_date", date_str) \
                .maybe_single() \
                .execute()
                
            return response.data
        except Exception as e:
            logger.error("snapshot_fetch_date_error", error=str(e))
            return None
            
    def get_snapshot_df(self, date_str: Optional[str] = None) -> pd.DataFrame:
        """Helper to get a DataFrame from a snapshot."""
        if date_str:
            data = self.get_snapshot_by_date(date_str)
        else:
            data = self.get_latest_snapshot()
            
        if data and 'assets' in data:
            df = pd.DataFrame(data['assets'])
            if 'super_score' in df.columns:
                 df = df.sort_values('super_score', ascending=False)
            return df
            
        return pd.DataFrame() # Empty
