"""
Script to seed default admin configuration in Supabase.
Run this once after creating the admin_config table.
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from dotenv import load_dotenv
load_dotenv()

from api.services.supabase_client import get_client

DEFAULT_CONFIG = {
    "red_flags": {
        "div_trap_threshold": 0.15,
        "low_liq_threshold": 500000,
        "high_debt_threshold": 3.0,
        "low_margin_threshold": 0.03,
        "stagnant_growth_threshold": 0
    },
    "strategy_weights": {
        "graham": 1.0,
        "greenblatt": 1.5,
        "bazin": 1.0,
        "qualidade": 2.0
    },
    "report_settings": {
        "top_n_stocks": 10,
        "show_cyclical_warning": True,
        "show_regulated_warning": True,
        "show_stagnant_warning": True
    },
    "filter_settings": {
        "dedup_enabled": True,
        "liquidity_score_cap": 50.0
    }
}

def seed_config():
    print("🌱 Seeding admin_config table...")
    
    client = get_client()
    if not client:
        print("❌ Failed to connect to Supabase")
        return False
    
    try:
        for key, value in DEFAULT_CONFIG.items():
            result = client.table("admin_config").upsert({
                "key": key,
                "value": value
            }).execute()
            print(f"  ✅ {key} -> inserted")
        
        print("\n🎉 Done! Configuration seeded successfully.")
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    seed_config()
