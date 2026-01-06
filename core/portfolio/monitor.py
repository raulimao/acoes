
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
        snapshot_map = {item.get('ticker', item.get('papel')): item for item in snapshot_assets}
        
        # 2. Parallel Live Fetching from TradingView
        # Limit live fetching to Top 30 for the active list
        monitoring_limit = 30
        active_portfolio = snapshot_assets[:30] # We still track 30 in the list
        tickers_to_fetch = [d.get('ticker', d.get('papel')) for d in active_portfolio[:monitoring_limit] if d.get('ticker', d.get('papel'))]
        
        live_results = {} # ticker -> {price, score}
        from tradingview_ta import get_multiple_analysis, Interval
        
        # Prepare symbols in format "EXCHANGE:TICKER"
        symbols_to_fetch = [f"BMFBOVESPA:{t}" for t in tickers_to_fetch]
        
        try:
            logger.info("daily_monitor_fetching_batch", count=len(symbols_to_fetch))
            batch_results = get_multiple_analysis(
                screener="brazil",
                interval=Interval.INTERVAL_1_DAY,
                symbols=symbols_to_fetch
            )
            for full_symbol, analysis in batch_results.items():
                if analysis:
                    ticker = full_symbol.split(":")[1]
                    price = analysis.indicators.get("close", 0)
                    summary = analysis.summary
                    buy = summary.get('BUY', 0)
                    sell = summary.get('SELL', 0)
                    total = buy + sell + summary.get('NEUTRAL', 1)
                    score = ((buy - sell + total) / (2 * total)) * 100
                    live_results[ticker] = {"price": price, "score": round(score, 2)}
        except Exception as e:
            logger.error("batch_fetch_failed", error=str(e))

        # 3. Fallbacks (Cache and Market Data)
        try:
            from pathlib import Path
            import json
            PROJECT_ROOT = Path(__file__).parent.parent.parent
            CACHE_FILE = PROJECT_ROOT / "data" / "technical_scores_cache.json"
            if CACHE_FILE.exists():
                with open(CACHE_FILE, 'r') as f:
                    cache_json = json.load(f)
                    tech_cache = cache_json.get("data", {})
        except Exception as e:
            logger.error("daily_monitor_cache_fallback_error", error=str(e))

        current_df = get_market_data()
            
        # 4. Compare and Detect Issues
        alerts = {
            "stop_loss": [],
            "red_flags": [],
            "portfolio_assets": [],
            "summary": {
                "checked_assets": 0,
                "total_snapshot_assets": len(snapshot_assets),
                "snapshot_date": snapshot_date,
                "data_source": "TradingView Live" if live_results else "TradingView Cache",
                "avg_pnl": 0.0,
                "best_performer": {"ticker": "N/A", "pnl": 0.0},
                "worst_performer": {"ticker": "N/A", "pnl": 0.0},
                "coverage_pct": 0.0,
                "positive_breadth": 0,
                "negative_breadth": 0
            }
        }
        
        all_pnls = []
        
        for i, old_data in enumerate(active_portfolio):
            ticker = old_data.get('ticker', old_data.get('papel'))
            rank = i + 1
            if not ticker: continue

            alerts["summary"]["checked_assets"] += 1
            
            current_price = 0.0
            current_score = 0.0
            current_flags = []
            
            # A. Priority 1: Live Result
            if ticker in live_results:
                current_price = live_results[ticker]["price"]
                current_score = live_results[ticker]["score"]
            
            # B. Priority 2: Tech Cache Fallback
            if current_price == 0 and ticker in tech_cache:
                asset_tech = tech_cache.get(ticker, {})
                current_price = asset_tech.get("indicators", {}).get("close", 0)
                current_score = asset_tech.get("summary_score", 0) * 100
            
            # C. Priority 3: Market Data Fallback + Flags
            current_row = current_df[current_df['papel'] == ticker] if not current_df.empty else pd.DataFrame()
            if not current_row.empty:
                row = current_row.iloc[0]
                if current_price == 0:
                    current_price = row.get('cotacao') or 0
                if current_score == 0:
                    current_score = row.get('super_score') or 0
                
                # Robust flag handling
                raw_flags = row.get('red_flags')
                if isinstance(raw_flags, list):
                    current_flags = raw_flags
                elif isinstance(raw_flags, str) and raw_flags.strip():
                    try:
                        import json
                        current_flags = json.loads(raw_flags.replace("'", '"'))
                        if not isinstance(current_flags, list): current_flags = []
                    except:
                        current_flags = []
                else:
                    current_flags = []

            asset_status = {
                "rank": rank,
                "ticker": ticker,
                "sector": old_data.get('sector') or old_data.get('setor') or 'N/A',
                "entry_price": old_data.get('price') or old_data.get('cotacao') or 0.0,
                "current_price": current_price or 0.0,
                "pnl_pct": 0.0,
                "current_score": round(current_score or 0.0, 2),
                "status": "OK"
            }
            
            if current_price > 0:
                entry_price = asset_status["entry_price"]
                if entry_price > 0:
                    pnl = (current_price - entry_price) / entry_price
                    pnl_pct = round(pnl * 100, 2)
                    asset_status["pnl_pct"] = pnl_pct
                    all_pnls.append(pnl_pct)
                    
                    if pnl_pct > 0: alerts["summary"]["positive_breadth"] += 1
                    elif pnl_pct < 0: alerts["summary"]["negative_breadth"] += 1
                    
                    if pnl <= STOP_LOSS_THRESHOLD:
                        asset_status["status"] = "STOP LOSS"
                        alerts["stop_loss"].append({
                            "ticker": ticker, "entry_price": entry_price, 
                            "current_price": current_price, "pnl_pct": asset_status["pnl_pct"],
                            "rank_at_snapshot": rank
                        })
                
                # Red Flags Check
                old_raw = old_data.get('red_flags', [])
                if not isinstance(old_raw, list): old_raw = []
                new_flags = set(current_flags) - set(old_raw)
                if new_flags:
                    if asset_status["status"] == "OK": asset_status["status"] = "ALERTA"
                    alerts["red_flags"].append({"ticker": ticker, "new_flags": list(new_flags)})
            else:
                asset_status["status"] = "SEM DADOS"
            
            alerts["portfolio_assets"].append(asset_status)
            
        # 5. Finalize Summary Statistics
        if all_pnls:
            alerts["summary"]["avg_pnl"] = round(sum(all_pnls) / len(all_pnls), 2)
            
            # Find Best and Worst from monitored list
            sorted_assets = sorted(alerts["portfolio_assets"], key=lambda x: x.get("pnl_pct", 0), reverse=True)
            if sorted_assets:
                best = sorted_assets[0]
                worst = sorted_assets[-1]
                alerts["summary"]["best_performer"] = {"ticker": best["ticker"], "pnl": best["pnl_pct"]}
                alerts["summary"]["worst_performer"] = {"ticker": worst["ticker"], "pnl": worst["pnl_pct"]}

        if alerts["summary"]["total_snapshot_assets"] > 0:
            alerts["summary"]["coverage_pct"] = round(
                (alerts["summary"]["checked_assets"] / alerts["summary"]["total_snapshot_assets"]) * 100, 1
            )
                
        logger.info("daily_monitor_finished", 
                    live_hits=len(live_results),
                    tracked_assets=len(alerts["portfolio_assets"]))
                    
        return alerts

                    
        return alerts

def extract_rank(asset_data: dict) -> int:
    # If we sorted before saving, we could infer rank, or if we saved 'rank' field.
    # SnapshotManager saves list sorted by super_score.
    # But inside the dict item, we might not have 'rank' explicit.
    # We can assume the consumer knows the rank or we just report the ticker.
    return 0 
