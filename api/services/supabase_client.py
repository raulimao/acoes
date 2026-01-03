"""
Supabase Client Service
Handles connection and operations with Supabase database
"""
from config.settings import SUPABASE_URL, SUPABASE_KEY, SUPABASE_SERVICE_KEY

# Placeholder for Supabase client
# Will be configured when SUPABASE_URL and SUPABASE_KEY are set

_client = None


def get_client():
    """
    Get Supabase client instance (lazy initialization).
    Prefers SUPABASE_SERVICE_KEY for backend operations (Bypass RLS).
    
    Returns:
        Supabase client or None if not configured
    """
    global _client
    
    if not SUPABASE_URL or (not SUPABASE_KEY and not SUPABASE_SERVICE_KEY):
        print("⚠️ Supabase não configurado. Configure SUPABASE_URL e CHAVES no .env")
        return None
    
    if _client is None:
        try:
            from supabase import create_client
            # Prioritize Service Key for Backend/Admin scripts
            key_to_use = SUPABASE_SERVICE_KEY if SUPABASE_SERVICE_KEY else SUPABASE_KEY
            _client = create_client(SUPABASE_URL, key_to_use)
            if key_to_use == SUPABASE_SERVICE_KEY:
                print("🔒 Supabase Client: Running with SERVICE ROLE (Admin)")
            else:
                print("👤 Supabase Client: Running with ANON KEY")
                
        except ImportError:
            print("⚠️ Instale supabase: pip install supabase")
            return None
    
    return _client


def is_configured() -> bool:
    """Check if Supabase is configured."""
    return bool(SUPABASE_URL and SUPABASE_KEY)
