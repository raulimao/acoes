"""
Authentication Service using Supabase
Handles user registration and authentication via Supabase PostgreSQL
"""
import os
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

# Initialize Supabase client
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY")  # Use service key for backend operations

# Fallback for development if no service key
if not SUPABASE_SERVICE_KEY:
    SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_KEY")

supabase: Client = None

def get_supabase_client() -> Client:
    """Get or create Supabase client."""
    global supabase
    if supabase is None:
        if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
            raise ValueError("SUPABASE_URL and SUPABASE_SERVICE_KEY must be set")
        supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)
    return supabase


def initialize_database():
    """
    Initialize database connection (Supabase handles table creation via migrations).
    This function is kept for compatibility but doesn't create tables.
    """
    # Just verify connection
    try:
        client = get_supabase_client()
        return client, None  # Return client for compatibility
    except Exception as e:
        print(f"Warning: Could not connect to Supabase: {e}")
        return None, None


def get_user_by_email(email: str):
    """
    Retrieve user data by email from Supabase profiles table.
    
    Args:
        email: Email to look up
        
    Returns:
        Tuple (username, name, email, password_hash, is_premium) or None if not found
    """
    try:
        client = get_supabase_client()
        result = client.table("profiles").select("*").ilike("email", email).maybe_single().execute()
        
        if result.data:
            profile = result.data
            return (
                profile.get("username"),
                profile.get("name"),
                profile.get("email"),
                None,  # No password hash for OAuth users
                profile.get("is_premium", False)
            )
        return None
    except Exception as e:
        print(f"Error getting user by email: {e}")
        return None


def ensure_profile_exists(email: str) -> bool:
    """
    Ensure profile exists in database, create from auth.users if missing.
    This fixes the issue where OAuth users exist in auth.users but not in profiles.
    
    Args:
        email: User email to check/create profile for
        
    Returns:
        True if profile exists or was created, False on error
    """
    try:
        client = get_supabase_client()
        
        # Check if profile exists
        existing = client.table("profiles").select("id").ilike("email", email).maybe_single().execute()
        if existing.data:
            return True
        
        # Profile missing - get user from auth.users
        users = client.auth.admin.list_users()
        for user in users:
            if user.email and user.email.lower() == email.lower():
                # Create profile from auth data
                name = (user.user_metadata or {}).get("name") or \
                       (user.user_metadata or {}).get("full_name") or \
                       email
                username = (user.user_metadata or {}).get("username") or \
                           email.split("@")[0]
                
                client.table("profiles").upsert({
                    "id": user.id,
                    "email": user.email,
                    "name": name,
                    "username": username,
                    "is_premium": False
                }).execute()
                print(f"Created missing profile for OAuth user: {email}")
                return True
        
        print(f"No auth user found for email: {email}")
        return False
    except Exception as e:
        print(f"Error ensuring profile exists: {e}")
        return False


def add_user(username: str, name: str, email: str, password: str = None, is_premium: bool = False) -> bool:
    """
    Add a new user profile to Supabase (for OAuth users).
    Note: For OAuth, the user is created in auth.users by Supabase automatically.
    This creates/updates the profile entry.
    
    Args:
        username: Unique username
        name: Full name
        email: User email
        password: Not used for OAuth (kept for compatibility)
        is_premium: Whether user has premium access
        
    Returns:
        True if user added/updated successfully, False otherwise
    """
    try:
        client = get_supabase_client()
        
        # Check if profile exists (case insensitive)
        existing = client.table("profiles").select("*").ilike("email", email).execute()
        
        if existing.data and len(existing.data) > 0:
            # Update existing profile
            client.table("profiles").update({
                "name": name,
                "username": username
            }).ilike("email", email).execute()
        else:
            # For OAuth users, get the auth user ID first
            # If no auth user exists, create profile with email as temporary ID
            auth_users = client.auth.admin.list_users()
            user_id = None
            
            for user in auth_users:
                if user.email == email:
                    user_id = user.id
                    break
            
            if user_id:
                client.table("profiles").upsert({
                    "id": user_id,
                    "username": username,
                    "name": name,
                    "email": email,
                    "is_premium": is_premium
                }).execute()
            else:
                # Create profile without auth user (will be linked later)
                # Using email hash as temporary ID
                import hashlib
                temp_id = hashlib.md5(email.encode()).hexdigest()
                client.table("profiles").upsert({
                    "id": temp_id,
                    "username": username,
                    "name": name,
                    "email": email,
                    "is_premium": is_premium
                }, on_conflict="email").execute()
        
        return True
    except Exception as e:
        print(f"Error adding user: {e}")
        return False




def register_supabase_user(username: str, name: str, email: str, password: str) -> tuple[bool, str]:
    """
    Register a new user via Supabase Auth (Sign Up).
    This ensures the user exists in auth.users before creating the profile.
    
    Returns:
        Tuple of (success: bool, message: str)
        - (True, "success") if registration succeeded
        - (True, "confirm_email") if user created but needs email confirmation
        - (False, "error_message") if registration failed
    """
    try:
        client = get_supabase_client()
        
        # 1. Sign Up in Supabase Auth
        res = client.auth.sign_up({
            "email": email,
            "password": password,
            "options": {
                "data": { "name": name, "username": username }
            }
        })
        
        # Check if user was created
        if not res.user:
            print(f"Sign up failed: no user returned")
            return (False, "Erro ao criar conta. Tente novamente.")
        
        user_id = res.user.id
        
        # Check if email confirmation is required
        # If user exists but session is None, email confirmation is pending
        if res.user and res.session is None:
            # User created, awaiting email confirmation
            # The trigger should create the profile, but let's ensure it exists
            try:
                client.table("profiles").upsert({
                    "id": user_id,
                    "username": username,
                    "name": name,
                    "email": email,
                    "is_premium": False
                }).execute()
            except Exception as profile_err:
                print(f"Profile creation note (may be handled by trigger): {profile_err}")
            
            return (True, "confirm_email")
        
        # 2. User created with session (email confirmation not required)
        # Create/update profile
        try:
            client.table("profiles").upsert({
                "id": user_id,
                "username": username,
                "name": name,
                "email": email,
                "is_premium": False
            }).execute()
        except Exception as profile_err:
            print(f"Profile creation note: {profile_err}")
        
        return (True, "success")
    
    except Exception as e:
        error_msg = str(e).lower()
        print(f"Error registering supabase user: {e}")
        
        # Check for specific errors
        if "already registered" in error_msg or "already exists" in error_msg:
            return (False, "Este email já está cadastrado. Tente fazer login.")
        if "invalid email" in error_msg:
            return (False, "Email inválido. Verifique e tente novamente.")
        if "weak password" in error_msg or "password" in error_msg:
            return (False, "Senha muito fraca. Use pelo menos 6 caracteres.")
        
        return (False, "Erro ao criar conta. Tente novamente.")


def upsert_oauth_user(email: str, name: str):
    """Ensure OAuth user exists in profiles table."""
    username = email.split("@")[0]
    return add_user(username, name, email)

def verify_user(email: str, password: str):
    """
    Verify user credentials.
    For Supabase OAuth, we don't verify passwords - authentication is handled by Supabase Auth.
    This function is kept for compatibility with email/password login.
    
    Args:
        email: User email
        password: Plain text password (not used for OAuth)
        
    Returns:
        User dict with username, name, email, is_premium if valid, None otherwise
        Raises:
            Exception: If authentication fails with specific message
    """
    try:
        client = get_supabase_client()
        
        # For email/password auth, use Supabase Auth
        # Note: This requires email/password to be set up in Supabase Auth
        data = {
            "email": email,
            "password": password
        }
        
        auth_response = client.auth.sign_in_with_password(data)
        
        if auth_response.user:
            # Check if email is confirmed (Supabase might return user even if not confirmed but sessions might be restricted)
            # However, usually sign_in throws error if config requires confirmation.
            
            # Get profile data
            profile = client.table("profiles").select("*").eq("email", email).single().execute()
            
            if profile.data:
                return {
                    "username": profile.data.get("username"),
                    "name": profile.data.get("name"),
                    "email": profile.data.get("email"),
                    "is_premium": profile.data.get("is_premium", False)
                }
        
        return None
    except Exception as e:
        # Check for specific "Email not confirmed" error message from Supabase
        error_msg = str(e).lower()
        if "email not confirmed" in error_msg:
            raise Exception("EmailNotConfirmed")
        
        print(f"Error verifying user: {e}") # Keep this for debugging
        return None


def resend_confirmation_email(email: str) -> bool:
    """
    Resend the signup confirmation email to the user.
    """
    try:
        client = get_supabase_client()
        client.auth.resend({
            "type": "signup",
            "email": email,
            "options": {
                "emailRedirectTo": f"{os.getenv('NEXT_PUBLIC_APP_URL', 'http://localhost:3000')}/auth/callback"
            }
        })
        return True
    except Exception as e:
        print(f"Error resending confirmation: {e}")
        return False


def get_user(username: str):
    """
    Retrieve user data by username.
    
    Args:
        username: Username to look up
        
    Returns:
        User tuple or None if not found
    """
    try:
        client = get_supabase_client()
        result = client.table("profiles").select("*").eq("username", username).single().execute()
        
        if result.data:
            return result.data
        return None
    except Exception as e:
        print(f"Error getting user: {e}")
        return None


def get_all_users() -> dict:
    """
    Get all users (for admin purposes).
    
    Returns:
        Dict with credentials format
    """
    try:
        client = get_supabase_client()
        result = client.table("profiles").select("*").execute()
        
        credentials = {"usernames": {}}
        
        for profile in result.data or []:
            credentials["usernames"][profile.get("username")] = {
                "name": profile.get("name"),
                "email": profile.get("email"),
                "is_premium": profile.get("is_premium", False)
            }
        
        return credentials
    except Exception as e:
        print(f"Error getting all users: {e}")
        return {"usernames": {}}


def update_user_premium(email: str, is_premium: bool) -> bool:
    """
    Update user premium status.
    
    Args:
        email: User email
        is_premium: New premium status
        
    Returns:
        True if updated successfully
    """
    try:
        client = get_supabase_client()
        client.table("profiles").update({
            "is_premium": is_premium
        }).ilike("email", email).execute()
        return True
    except Exception as e:
        print(f"Error updating premium status: {e}")
        return False
