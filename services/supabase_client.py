"""
Supabase Client Service
Handles connection and operations with Supabase database
"""
from config.settings import SUPABASE_URL, SUPABASE_KEY

# Placeholder for Supabase client
# Will be configured when SUPABASE_URL and SUPABASE_KEY are set

_client = None


def get_client():
    """
    Get Supabase client instance (lazy initialization).
    
    Returns:
        Supabase client or None if not configured
    """
    global _client
    
    if not SUPABASE_URL or not SUPABASE_KEY:
        print("⚠️ Supabase não configurado. Configure SUPABASE_URL e SUPABASE_KEY no .env")
        return None
    
    if _client is None:
        try:
            from supabase import create_client
            _client = create_client(SUPABASE_URL, SUPABASE_KEY)
        except ImportError:
            print("⚠️ Instale supabase: pip install supabase")
            return None
    
    return _client


def is_configured() -> bool:
    """Check if Supabase is configured."""
    return bool(SUPABASE_URL and SUPABASE_KEY)
