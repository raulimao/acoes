"""
Admin Configuration Service
Manages dynamic configuration for scoring thresholds, strategy weights, and report settings.
Stores configuration in Supabase for persistence.
"""
import json
from typing import Dict, Any, Optional
from api.services.supabase_client import get_client
import structlog

logger = structlog.get_logger()

# Default configuration (fallback if DB is unavailable)

from config.strategies_config import (
    DEFAULT_RED_FLAGS, 
    DEFAULT_REPORT_SETTINGS, 
    DEFAULT_FILTER_SETTINGS
)

# Default configuration (fallback if DB is unavailable)
DEFAULT_CONFIG = {
    "red_flags": DEFAULT_RED_FLAGS,
    "strategy_weights": {
        "graham": 1.0, 
        "greenblatt": 1.5,
        "bazin": 1.0,
        "qualidade": 2.0
    }, # This part is still partially duplicated but strategy_weights structure is simpler here
    "report_settings": DEFAULT_REPORT_SETTINGS,
    "filter_settings": DEFAULT_FILTER_SETTINGS
}


# In-memory cache
_config_cache: Optional[Dict[str, Any]] = None


def get_config() -> Dict[str, Any]:
    """
    Get current configuration.
    Tries Supabase first, falls back to defaults.
    
    Returns:
        Full configuration dictionary
    """
    global _config_cache
    
    # Return cache if available
    if _config_cache is not None:
        return _config_cache
    
    # Try to load from Supabase
    try:
        client = get_client()
        if client:
            response = client.table("admin_config").select("key, value").execute()
            
            if response.data:
                config = DEFAULT_CONFIG.copy()
                for row in response.data:
                    key = row.get("key")
                    value = row.get("value")
                    if key and value:
                        config[key] = value
                
                _config_cache = config
                logger.info("config_loaded_from_db", keys=list(config.keys()))
                return config
                
    except Exception as e:
        logger.warning("config_db_load_failed", error=str(e))
    
    # Fallback to defaults
    logger.info("config_using_defaults")
    _config_cache = DEFAULT_CONFIG.copy()
    return _config_cache


def update_config(key: str, value: Dict[str, Any]) -> bool:
    """
    Update a configuration section.
    
    Args:
        key: Config section (red_flags, strategy_weights, etc.)
        value: New values for that section
        
    Returns:
        True if successful
    """
    global _config_cache
    
    try:
        client = get_client()
        if not client:
            logger.error("config_update_failed_no_client")
            return False
        
        # Upsert to DB
        client.table("admin_config").upsert({
            "key": key,
            "value": value
        }).execute()
        
        # Invalidate cache
        _config_cache = None
        
        logger.info("config_updated", key=key)
        return True
        
    except Exception as e:
        logger.error("config_update_failed", key=key, error=str(e))
        return False


def invalidate_cache():
    """Force reload of configuration on next get_config() call."""
    global _config_cache
    _config_cache = None
    logger.info("config_cache_invalidated")


# ============ HELPER FUNCTIONS FOR CALCULATOR ============

def get_red_flag_thresholds() -> Dict[str, float]:
    """Get red flag thresholds for calculator.py"""
    config = get_config()
    return config.get("red_flags", DEFAULT_CONFIG["red_flags"])


def get_strategy_weights() -> Dict[str, float]:
    """Get strategy weights for scoring."""
    config = get_config()
    return config.get("strategy_weights", DEFAULT_CONFIG["strategy_weights"])


def get_report_settings() -> Dict[str, Any]:
    """Get report generation settings."""
    config = get_config()
    return config.get("report_settings", DEFAULT_CONFIG["report_settings"])


def get_filter_settings() -> Dict[str, Any]:
    """Get data filtering settings."""
    config = get_config()
    return config.get("filter_settings", DEFAULT_CONFIG["filter_settings"])
