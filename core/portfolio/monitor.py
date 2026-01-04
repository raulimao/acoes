
"""
Daily Portfolio Monitor
Checks for Stop Loss triggers and New Red Flags against the weekly snapshot.
"""
import pandas as pd
from typing import List, Dict, Any
import structlog
from datetime import datetime

from core.portfolio.manager import SnapshotManager
from api.services.data_service import get_market_data

logger = structlog.get_logger()

# Configuration
STOP_LOSS_THRESHOLD = -0.10  # -10% drop from snapshot price

class DailyMonitor:
    def __init__(self):
        self.snapshot_manager = SnapshotManager()
        
    def run_check(self) -> Dict[str, List[Dict]]:
        """
        Main execution method.
        Compares Current Market Data vs Latest Snapshot.
        Returns a dict with 'stop_loss_alerts' and 'red_flag_alerts'.
        """
        logger.info("daily_monitor_start")
        
        # 1. Load Latest Snapshot (The "Official Portfolio")
        snapshot_data = self.snapshot_manager.get_latest_snapshot()
        if not snapshot_data:
            logger.warning("daily_monitor_no_snapshot")
            return {}
            
        snapshot_date = snapshot_data.get('snapshot_date')
        snapshot_assets = snapshot_data.get('assets', [])
        
        # Convert snapshot to dict for O(1) lookup
        # We only care about the assets that were in the portfolio (e.g., Top 10 or Top 20)
        # For safety, let's monitor the entire snapshot list (Top 100 usually).
        # But alerts are most critical for the Top picks. Let's assume user holds Top 10.
        
        # Strategy: Monitor ALL items in snapshot, but highlight Rank.
        snapshot_map = {item['papel']: item for item in snapshot_assets}
        
        # 2. Load Current Market Data
        current_df = get_market_data()
        if current_df.empty:
            logger.error("daily_monitor_no_live_data")
            return {}
            
        # 3. Compare and Detect Issues
        alerts = {
            "stop_loss": [],
            "red_flags": [],
            "portfolio_assets": [], # New: Full list of tracked assets
            "summary": {
                "checked_assets": 0,
                "snapshot_date": snapshot_date
            }
        }
        
        # We only care about the explicit Top items from the snapshot for the "Portfolio" view.
        # Assuming the snapshot list is sorted by rank.
        # Let's track the Top 25 as the "Active Portfolio".
        active_portfolio = snapshot_assets[:25]
        
        for i, old_data in enumerate(active_portfolio):
            ticker = old_data.get('papel')
            rank = i + 1
            
            alerts["summary"]["checked_assets"] += 1
            
            # Find current data
            current_row = current_df[current_df['papel'] == ticker]
            
            asset_status = {
                "rank": rank,
                "ticker": ticker,
                "sector": old_data.get('setor', 'N/A'),
                "entry_price": old_data.get('cotacao', 0),
                "current_price": 0.0,
                "pnl_pct": 0.0,
                "current_score": 0.0,
                "status": "OK"
            }
            
            if not current_row.empty:
                row = current_row.iloc[0]
                current_price = row.get('cotacao', 0)
                entry_price = old_data.get('cotacao', 0)
                asset_status["current_price"] = current_price
                asset_status["current_score"] = row.get('super_score', 0)
                
                # Check 1: Stop Loss
                if current_price > 0 and entry_price > 0:
                    pnl = (current_price - entry_price) / entry_price
                    asset_status["pnl_pct"] = round(pnl * 100, 2)
                    
                    if pnl <= STOP_LOSS_THRESHOLD:
                        asset_status["status"] = "STOP LOSS"
                        alerts["stop_loss"].append({
                            "ticker": ticker,
                            "entry_price": entry_price,
                            "current_price": current_price,
                            "pnl_pct": round(pnl * 100, 2),
                            "rank_at_snapshot": rank
                        })
                
                # Check 2: Red Flags
                current_raw = row.get('red_flags')
                if not isinstance(current_raw, list):
                    current_raw = []
                
                old_raw = old_data.get('red_flags')
                if not isinstance(old_raw, list):
                    old_raw = []
                    
                new_flags = set(current_raw) - set(old_raw)
                
                if new_flags:
                    if asset_status["status"] == "OK":
                        asset_status["status"] = "ALERTA"
                    
                    alerts["red_flags"].append({
                        "ticker": ticker,
                        "new_flags": list(new_flags),
                        "current_flags": list(current_raw)
                    })
            else:
                asset_status["status"] = "SEM DADOS"
            
            alerts["portfolio_assets"].append(asset_status)
                
        logger.info("daily_monitor_finished", 
                    stop_losses=len(alerts["stop_loss"]), 
                    new_flags=len(alerts["red_flags"]),
                    tracked_assets=len(alerts["portfolio_assets"]))
                    
        return alerts

def extract_rank(asset_data: dict) -> int:
    # If we sorted before saving, we could infer rank, or if we saved 'rank' field.
    # SnapshotManager saves list sorted by super_score.
    # But inside the dict item, we might not have 'rank' explicit.
    # We can assume the consumer knows the rank or we just report the ticker.
    return 0 
