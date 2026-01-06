
import pandas as pd
import sys
from pathlib import Path
import traceback

# DEBUG LOGGING
DEBUG_FILE = Path(__file__).parent.parent.parent / "fusion_debug.txt"

def log_debug(msg):
    with open(DEBUG_FILE, "a") as f:
        f.write(f"{pd.Timestamp.now()} - {msg}\n")

# Add ProjecaoAcoes to path
try:
    PROJECT_ROOT = Path(__file__).parent.parent.parent
    PROJECAO_PATH = PROJECT_ROOT / "ProjecaoAcoes"
    if str(PROJECAO_PATH) not in sys.path:
        sys.path.append(str(PROJECAO_PATH))
    log_debug(f"Sys Path Updated. Projecao Path: {PROJECAO_PATH}")
except Exception as e:
    log_debug(f"Error setting path: {e}")

# Global checks removed, will import lazily

# IMPORT FIX: Match main.py import to share Singleton RAM Cache
# main.py adds 'api' folder to sys.path, so 'services' is a top-level package there.
# We try to import 'services.data_service' first (API context).
# If that fails (e.g. running script), we try 'api.services.data_service'.

try:
    from services.data_service import get_market_data
    log_debug("Imported get_market_data from services (Shared Cache)")
except ImportError:
    from api.services.data_service import get_market_data
    log_debug("Imported get_market_data from api.services (Separate Cache)")

def get_fusion_ranking():
    """
    Generates the 'Perfect Stock' ranking by fusing:
    1. Fundamentalist Score (Super Score) - Weight 70%
    2. Technical Score (AI Probability) - Weight 30%
    """
    log_debug("get_fusion_ranking CALLED")
    
    # 1. Get Fundamentalist Data
    try:
        df_fund = get_market_data()
        log_debug(f"Market Data Rows: {len(df_fund)}")
        if df_fund.empty:
            return []
    except Exception as e:
        log_debug(f"Error getting market data: {e}")
        return []
    
    # FIXED: Use a fixed normalization factor (max points possible is ~25-30)
    # This prevents the 'bubble' where the top stock always becomes 100% fundamental
    # even if its absolute points are low.
    NORM_BASE = 25.0 
    df_fund['fund_norm'] = df_fund['super_score'] / NORM_BASE
    # Cap at 1.0
    df_fund['fund_norm'] = df_fund['fund_norm'].clip(upper=1.0)
    
    # 2. Get Technical Data (Optimized: Read from JSON Cache - RICH DATA)
    tech_data = {} # ticker -> {score, rsi, ema200, close, signal...}
    
    try:
        # Define Cache Path
        PROJECT_ROOT = Path(__file__).parent.parent.parent
        CACHE_FILE = PROJECT_ROOT / "data" / "technical_scores_cache.json"
        
        if CACHE_FILE.exists():
            import json
            with open(CACHE_FILE, 'r') as f:
                cache_data = json.load(f)
                # NEW: Read from 'data' key (rich format)
                tech_data = cache_data.get("data", {})
            log_debug(f"Technical Data loaded from cache: {len(tech_data)} items")
        else:
            log_debug(f"Technical Cache not found at {CACHE_FILE}")
            
    except Exception as e:
        log_debug(f"Error reading technical cache: {e}")
        tech_data = {}

    # 3. Fusion + Timing Signal Calculation
    ranking = []
    
    try:
        for _, row in df_fund.iterrows():
            ticker = row['papel']
            fund_score = row['fund_norm'] # 0-1
            
            # Get Rich Technical Data for this ticker
            asset_tech = tech_data.get(ticker, {})
            
            # Extract required fields (with fallbacks)
            tech_score = asset_tech.get("summary_score", 0.5) # 0-1
            indicators = asset_tech.get("indicators", {})
            
            # FIX: Handle None values from cache by using 'or' fallback
            rsi = indicators.get("RSI") or 50.0
            ema200 = indicators.get("EMA200") or 0.0
            close_price = indicators.get("close") or row.get('cotacao', 0) or 0.0
            tv_signal = asset_tech.get("summary_signal", "NEUTRAL")
            
            # --- TIMING SIGNAL LOGIC ---
            # Compares Price vs EMA200 (Trend) and RSI (Momentum)
            timing_signal = "NEUTRO"
            timing_emoji = "⚪"
            
            if ema200 > 0: # Only calculate if EMA200 exists
                price_above_ema200 = close_price > ema200
                
                if price_above_ema200:
                    if rsi < 70:
                        timing_signal = "ÓTIMO"
                        timing_emoji = "🟢"
                    else:
                        timing_signal = "ESTICADO" # Tendência Alta mas RSI alto
                        timing_emoji = "⚪"
                else: # Preço abaixo da EMA200 (Tendência Baixa)
                    if rsi < 30:
                        timing_signal = "BARGANHA"
                        timing_emoji = "🟡"
                    else:
                        timing_signal = "PERIGO"
                        timing_emoji = "🔴"
            else:
                timing_signal = "SEM_DADOS"
                timing_emoji = "⚫"
            
            # Fusion Formula (70% Fund, 30% Tech)
            fusion_score = (fund_score * 0.7) + (tech_score * 0.3)
            
            # --- RISK PENALTIES (BLIND SPOT FIXES) ---
            risk_alert = None
            
            # 1. Liquidity Penalty (Crush Score for Illiquid Stocks)
            liq_vol = row.get('liquidez_2meses') or row.get('volume') or 0
            if liq_vol < 500_000:
                fusion_score *= 0.1 # Decimate score
                risk_alert = "RISCO (ILIQUIDEZ)"
                
            # 2. Payout Penalty (Unstainable Dividends)
            pl_val = row.get('p_l', 0) or 0
            dy_val = row.get('dividend_yield', 0) or 0
            payout_ratio = dy_val * pl_val
            if payout_ratio > 1.2 and dy_val > 0.10: # Only if High Yield > 10%
                fusion_score *= 0.5 # Halve score
                risk_alert = "ALERTA (PAYOUT)"
                
            # 3. Debt Penalty (High Leverage)
            debt_equity = row.get('div_bruta_patrimonio', 0) or 0
            if debt_equity > 2.0:
                fusion_score *= 0.7 # Reduce by 30%
                risk_alert = "ALERTA (DÍVIDA)"

            # --- AI VERDICT CALCULATION (Simplified) ---
            # Combines fundamental + technical scoring for quick verdict
            fund_points = 0
            tech_points = 0
            
            # Fundamental scoring (from stock data)
            roe_val = row.get('roe', 0) or 0
            pvp_val = row.get('p_vp', 0) or 0
            
            # P/L scoring
            if 0 < pl_val < 10:
                fund_points += 3
            elif 0 < pl_val < 15:
                fund_points += 2
            elif pl_val > 25 or pl_val < 0:
                fund_points -= 2
            
            # Dividend scoring
            dy_pct = dy_val * 100 if dy_val < 1 else dy_val
            if dy_pct >= 6:
                fund_points += 3
            elif dy_pct >= 4:
                fund_points += 2
            
            # ROE scoring
            roe_pct = roe_val * 100 if roe_val < 1 else roe_val
            if roe_pct >= 20:
                fund_points += 3
            elif roe_pct >= 15:
                fund_points += 2
            elif roe_pct < 10:
                fund_points -= 1
            
            # P/VP scoring
            if 0 < pvp_val < 1:
                fund_points += 2
            elif pvp_val > 3:
                fund_points -= 1
            
            # Technical scoring
            if 'STRONG_BUY' in tv_signal:
                tech_points += 3
            elif 'BUY' in tv_signal:
                tech_points += 2
            elif 'STRONG_SELL' in tv_signal:
                tech_points -= 3
            elif 'SELL' in tv_signal:
                tech_points -= 2
            
            total_points = fund_points + tech_points
            
            # Determine verdict
            if risk_alert:
                ai_verdict = risk_alert.split(" ")[0] # "RISCO" or "ALERTA"
                ai_verdict_color = "red" if "RISCO" in risk_alert else "amber"
                ai_recommendation = risk_alert
            elif total_points >= 8:
                ai_verdict = "OPORTUNIDADE"
                ai_verdict_color = "emerald"
                ai_recommendation = "COMPRA FORTE"
            elif total_points >= 5:
                ai_verdict = "MUITO ATRATIVO"
                ai_verdict_color = "green"
                ai_recommendation = "COMPRA"
            elif total_points >= 2:
                ai_verdict = "ATRATIVO"
                ai_verdict_color = "cyan"
                ai_recommendation = "COMPRA MODERADA"
            elif total_points >= -1:
                ai_verdict = "NEUTRO"
                ai_verdict_color = "slate"
                ai_recommendation = "MANTER"
            elif total_points >= -4:
                ai_verdict = "CAUTELA"
                ai_verdict_color = "amber"
                ai_recommendation = "EVITAR"
            else:
                ai_verdict = "RISCO"
                ai_verdict_color = "red"
                ai_recommendation = "VENDA"
            
            ranking.append({
                "ticker": ticker,
                "company_name": row.get('empresa') or row.get('Empresa', 'N/A'),
                "sector": row.get('setor', 'N/A'),
                "price": row.get('cotacao', 0),
                "fund_score_raw": row.get('super_score', 0),
                "tech_prob": tech_score,
                "dy": row.get('dividend_yield', 0),
                "roe": row.get('roe', 0),
                "p_l": row.get('p_l', 0),
                "growth": row.get('crescimento_receita_5a', 0),
                "fusion_score": fusion_score * 100, # Scale to 0-100 for display
                "matches_tech": tech_score > 0.6,
                # Technical fields
                "tv_signal": tv_signal,
                "rsi": round(rsi, 1),
                "ema200": round(ema200, 2),
                "timing_signal": timing_signal,
                "timing_emoji": timing_emoji,
                # AI Verdict fields
                "ai_verdict": ai_verdict,
                "ai_verdict_color": ai_verdict_color,
                "ai_recommendation": ai_recommendation,
                "ai_fund_score": fund_points,
                "ai_tech_score": tech_points,
            })
            
        # Sort by Fusion Score
        ranking.sort(key=lambda x: x['fusion_score'], reverse=True)
        log_debug(f"Ranking generated with {len(ranking)} items")
    except Exception as e:
        log_debug(f"Error during fusion loop: {e}")
        traceback.print_exc()
    
    return ranking # Return All stocks (Caller handles limits)

if __name__ == "__main__":
    # Test
    r = get_fusion_ranking()
    for item in r[:10]:
        print(f"{item['ticker']} | Fusion: {item['fusion_score']:.1f} | Fund: {item['fund_score_raw']:.1f} | Tech: {item['tech_prob']:.2f}")
