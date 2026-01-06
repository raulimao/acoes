"""
FastAPI Backend for NorteAcoes Dashboard
Serves stock data, strategies, and history via REST API
"""
import sys
from pathlib import Path

# Load environment variables from .env file
from dotenv import load_dotenv
load_dotenv()

# Add project root and api directory to path
sys.path.insert(0, str(Path(__file__).parent.parent)) # Root (for core, utils)
sys.path.insert(0, str(Path(__file__).parent))        # API dir (for services)

from fastapi import FastAPI, HTTPException, Query, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field
from typing import List, Optional
import pandas as pd
from datetime import datetime, timedelta
from jose import JWTError, jwt
import os
import time
import structlog
from utils.logging_config import logger

from core.pipeline import carregar_dados_completos
from services.history_service import save_to_historico, get_historico
from core.integration import fusion
# from services.setores_service import get_all_setores (Removed)

from services.data_service import get_market_data, update_market_data_background
from services.ai_chat import ChatMessage, ChatRequest, process_chat, check_chat_limit

from services.auth_service import add_user, verify_user, get_user_by_email, initialize_database, update_user_premium, upsert_oauth_user, register_supabase_user, resend_confirmation_email, ensure_profile_exists
from services.payment_service import create_checkout_session, verify_webhook_signature, create_portal_session
from services.email_service import send_welcome_email, send_payment_success_email
from fastapi import FastAPI, HTTPException, Query, Depends, Request, BackgroundTasks
from fastapi.responses import StreamingResponse
from config.strategies_config import ESTRATEGIAS, FILTROS
from fpdf import FPDF
import io

# ... (rest of imports)

# ...



# JWT Configuration
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "topacoes-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7  # 7 days

security = HTTPBearer(auto_error=False)

# Initialize database on startup
initialize_database()

app = FastAPI(
    title="NorteAcoes API",
    description="API para análise fundamentalista de ações da B3",
    version="2.0.0"
)

# CORS for React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "https://acoes-liart.vercel.app",
        "https://acoes.vercel.app",
        "https://acoes.onrender.com"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Middleware for Logging and Performance
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()
    
    # Generate Request ID (simplified)
    request_id = str(int(time.time() * 1000))
    structlog.contextvars.bind_contextvars(request_id=request_id)
    
    logger.info("request_started", path=request.url.path, method=request.method, ip=request.client.host)
    
    try:
        response = await call_next(request)
        process_time = time.time() - start_time
        
        logger.info(
            "request_completed",
            path=request.url.path,
            status_code=response.status_code,
            duration=f"{process_time:.4f}s"
        )
        return response
    except Exception as e:
        process_time = time.time() - start_time
        logger.error(
            "request_failed",
            path=request.url.path,
            error=str(e),
            duration=f"{process_time:.4f}s",
            exc_info=True
        )
        # Re-raise so FastAPI exception handler catches it (or our global one)
        raise e

# Global Exception Handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error("unhandled_exception", error=str(exc), path=request.url.path, exc_info=True)
    return {
        "detail": "Internal Server Error",
        "message": "Ocorreu um erro inesperado. Nossa equipe foi notificada."
    }

# New Data Service Integration
# This replaces the old RAM-only cache with Supabase-backed persistence

@app.on_event("startup")
async def startup_event():
    """Load cache from DB on startup to avoid delay for first user."""
    logger.info("app_startup_preload")
    try:
        # This will load from Supabase to RAM
        get_market_data()
    except Exception as e:
        logger.error("startup_preload_failed", error=str(e))

def get_stock_data():
    """
    Proxy to the new DataService.
    Keeps compatibility with existing endpoints calling get_stock_data().
    """
    return get_market_data()



import importlib
from core.integration import fusion

@app.post("/api/admin/refresh-cache")
async def force_refresh(background_tasks: BackgroundTasks, key: str = Query(None)):
    """Force background data update (Admin)."""
    if key != os.getenv("ADMIN_KEY", "admin123"):
        raise HTTPException(status_code=403, detail="Forbidden")
        
    # Force reload modules
    importlib.reload(fusion)
    
    background_tasks.add_task(update_market_data_background)
    return {"status": "started", "message": "Scraper rodando em background..."}


@app.get("/api/cron/update")
async def cron_update(background_tasks: BackgroundTasks, key: str = Query(None)):
    """
    Standard Cron Endpoint for external schedulers (cron-job.org, GitHub Actions).
    Supports GET request which is easier for some cron services.
    """
    if key != os.getenv("CRON_SECRET", os.getenv("ADMIN_KEY", "admin123")):
        raise HTTPException(status_code=403, detail="Forbidden")
        
    logger.info("cron_triggered", source="external")
    
    # Import Orchestrator locally to avoid circular dependencies
    from api.services.orchestrator import run_daily_system_update
    
    background_tasks.add_task(run_daily_system_update)
    return {"status": "success", "message": "Full Daily Update (Safe Logic) Started"}



# ============================================
# ADMIN CONFIGURATION ENDPOINTS
# ============================================

from services.config_service import get_config, update_config, invalidate_cache, get_red_flag_thresholds

# Admin email whitelist (can be moved to env or DB later)
ADMIN_EMAILS = ["raulimaoliveira@gmail.com", "raulennonlima@gmail.com", "admin@norteacoes.com"]


class AdminConfigUpdate(BaseModel):
    key: str = Field(..., description="Config section: red_flags, strategy_weights, report_settings, filter_settings")
    value: dict = Field(..., description="New values for that section")


@app.get("/api/admin/config")
async def get_admin_config(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Get all configuration settings (admin only)."""
    user = await get_current_user(credentials)
    
    if not user or user.get("email") not in ADMIN_EMAILS:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    return get_config()


@app.post("/api/admin/config")
async def update_admin_config(
    update: AdminConfigUpdate,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Update a configuration section (admin only)."""
    user = await get_current_user(credentials)
    
    if not user or user.get("email") not in ADMIN_EMAILS:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    valid_keys = ["red_flags", "strategy_weights", "report_settings", "filter_settings"]
    if update.key not in valid_keys:
        raise HTTPException(status_code=400, detail=f"Invalid key. Must be one of: {valid_keys}")
    
    success = update_config(update.key, update.value)
    
    if success:
        return {"status": "success", "message": f"Config '{update.key}' updated", "new_value": update.value}
    else:
        raise HTTPException(status_code=500, detail="Failed to update config")


@app.post("/api/admin/config/reset")
async def reset_admin_config(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Reset config cache to reload from DB (admin only)."""
    user = await get_current_user(credentials)
    
    if not user or user.get("email") not in ADMIN_EMAILS:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    invalidate_cache()
    return {"status": "success", "message": "Config cache invalidated"}


# ============================================
# MODELS
# ============================================

class StockData(BaseModel):
    papel: str
    setor: Optional[str] = None
    subsetor: Optional[str] = None
    cotacao: Optional[float] = None
    p_l: Optional[float] = None
    p_vp: Optional[float] = None
    dividend_yield: Optional[float] = None
    roe: Optional[float] = None
    roic: Optional[float] = None
    score_graham: Optional[float] = None
    score_greenblatt: Optional[float] = None
    score_bazin: Optional[float] = None
    score_qualidade: Optional[float] = None
    super_score: Optional[float] = None
    fusion_score: Optional[float] = None


class StrategyInfo(BaseModel):
    name: str
    display_name: str
    weight: float
    description: str
    filters: List[str]


class DashboardStats(BaseModel):
    total_stocks: int
    avg_super_score: float
    top_stock: str
    top_score: float
    sectors_count: int
    opportunities_count: int
    toxic_count: int
    market_sentiment: str
    avg_dividend_yield: float
    avg_roe: float
    avg_pl: float
    best_sector: str
    avg_growth: float


# Auth Models
class LoginRequest(BaseModel):
    email: str
    password: str


class RegisterRequest(BaseModel):
    name: str = Field(..., min_length=2, description="Nome completo do usuário")
    email: str = Field(..., min_length=5, description="Email válido")
    password: str = Field(..., min_length=6, description="Senha com mínimo 6 caracteres")


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: dict


class UserResponse(BaseModel):
    username: str
    name: str
    email: str
    is_premium: bool = False


# ============================================
# JWT HELPER FUNCTIONS
# ============================================

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Create JWT access token."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Get current user from JWT token."""
    if not credentials:
        raise HTTPException(status_code=401, detail="Não autenticado")
    
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        name: str = payload.get("name", email.split("@")[0] if email else "User")
        if email is None:
            raise HTTPException(status_code=401, detail="Token inválido")
    except JWTError:
        raise HTTPException(status_code=401, detail="Token inválido")
    
    # Try to get user from database
    try:
        user = get_user_by_email(email)
        if user:
            # user tuple: (username, name, email, password, is_premium)
            return {
                "username": user[0], 
                "name": user[1], 
                "email": user[2],
                "is_premium": bool(user[4]) if len(user) > 4 else False
            }
    except Exception as e:
        print(f"Note: Could not fetch user from DB: {e}")
    
    # Fallback: return data from JWT (for OAuth users not in DB)
    return {
        "username": email.split("@")[0],
        "name": name,
        "email": email,
        "is_premium": False  # Default to non-premium for OAuth users
    }



# ============================================
# AUTH ENDPOINTS
# ============================================

class ResendConfirmationRequest(BaseModel):
    email: str

@app.post("/api/auth/resend-confirmation")
async def resend_confirmation(request: ResendConfirmationRequest):
    """Resend confirmation email to user."""
    # Always return success to prevent email enumeration (security best practice)
    # But log the result internally
    resend_confirmation_email(request.email)
    return {"message": "Se o email estiver cadastrado, uma nova confirmação será enviada."}


@app.post("/api/auth/login", response_model=TokenResponse)
async def login(request: LoginRequest):
    """Authenticate user and return JWT token."""
    try:
        user = verify_user(request.email, request.password)
    except Exception as e:
        if str(e) == "EmailNotConfirmed":
            raise HTTPException(
                status_code=403, 
                detail="Por favor, confirme seu email antes de fazer login. Verifique sua caixa de entrada."
            )
        raise e
    
    if not user:
        raise HTTPException(status_code=401, detail="Email ou senha incorretos")
    
    access_token = create_access_token(
        data={"sub": user["email"], "name": user["name"]}
    )
    
    return TokenResponse(
        access_token=access_token,
        user=user
    )


@app.post("/api/auth/register", response_model=TokenResponse)
async def register(request: RegisterRequest):
    """Register new user and return JWT token."""
    # Check if user already exists in profiles
    existing = get_user_by_email(request.email)
    if existing:
        raise HTTPException(status_code=400, detail="Email já cadastrado. Tente fazer login.")
    
    # Create username from email
    username = request.email.split("@")[0]
    
    # Register in Supabase Auth + Profile
    success, message = register_supabase_user(username, request.name, request.email, request.password)
    
    if not success:
        raise HTTPException(status_code=400, detail=message)
    
    # Handle email confirmation required
    if message == "confirm_email":
        # User created but needs to confirm email
        # Return a special response indicating this
        raise HTTPException(
            status_code=202,  # Accepted
            detail="Conta criada com sucesso! Verifique seu email para confirmar o cadastro."
        )
    
    # Create token (only if no email confirmation required)
    access_token = create_access_token(
        data={"sub": request.email, "name": request.name}
    )
    
    # Send welcome email
    try:
        send_welcome_email(request.name, request.email)
    except Exception as e:
        logger.error("welcome_email_failed", error=str(e))
    
    return TokenResponse(
        access_token=access_token,
        user={"username": username, "name": request.name, "email": request.email, "is_premium": False}
    )


@app.post("/api/auth/oauth-login", response_model=TokenResponse)
async def oauth_login(email: str, name: str, provider: str = "google"):
    """Login/register user from OAuth provider (Google, etc). No password needed.
    
    For OAuth users, we don't need to store them locally - Supabase Auth handles that.
    We just create a JWT for our API access.
    """
    username = email.split("@")[0]
    
    # For OAuth users, default to non-premium (can be upgraded later)
    # In production, you'd check Supabase profiles table for is_premium
    is_premium = False
    
    is_premium = False
    
    # Sync User to DB (Ensures profile exists for Premium upgrades)
    try:
        upsert_oauth_user(email, name)
    except Exception as e:
        logger.error("oauth_sync_failed", error=str(e))

    # Try to get existing user premium status from database
    try:
        existing = get_user_by_email(email)
        if existing and len(existing) >= 5:
            is_premium = bool(existing[4])
    except Exception as e:
        print(f"Note: Could not check user status from DB: {e}")
        # Continue without DB - user will be non-premium
    
    user_data = {
        "username": username,
        "name": name,
        "email": email,
        "is_premium": is_premium
    }
    
    # Create token
    access_token = create_access_token(
        data={"sub": email, "name": name}
    )
    
    return TokenResponse(
        access_token=access_token,
        user=user_data
    )




@app.get("/api/auth/me", response_model=UserResponse)
async def get_me(current_user: dict = Depends(get_current_user)):
    """Get current authenticated user info."""
    return current_user


# ============================================
# PAYMENT ENDPOINTS
# ============================================

class CheckoutRequest(BaseModel):
    return_url: str

@app.post("/api/payments/checkout")
async def create_checkout(
    request: CheckoutRequest,
    current_user: dict = Depends(get_current_user)
):
    """Create Stripe Checkout Session."""
    try:
        url = create_checkout_session(
            user_id=current_user.get("username", "unknown"),
            email=current_user["email"],
            base_url=request.return_url.rstrip("/")
        )
        return {"url": url}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/admin/force-upgrade")
async def admin_force_upgrade(email: str, key: str):
    """Emergency endpoint to upgrade user if webhook fails."""
    # Simple hardcoded key for now - user is the only admin
    if key != "admin_secret_123":
        raise HTTPException(status_code=403, detail="Forbidden")
    

    
    # Ensure user exists first (fix for OAuth ghosts)
    upsert_oauth_user(email, email.split("@")[0])
    
    success = update_user_premium(email, True)
    if success:
        return {"status": "success", "message": f"User {email} upgraded to Premium"}
    else:
        raise HTTPException(status_code=400, detail="User not found")

@app.post("/api/payments/portal")
async def create_portal(
    request: CheckoutRequest,  # reusing same model for return_url
    current_user: dict = Depends(get_current_user)
):
    """Create Stripe Customer Portal Session."""
    try:
        url = create_portal_session(
            email=current_user["email"],
            return_url=request.return_url.rstrip("/")
        )
        return {"url": url}
    except Exception as e:
        # If user is not customer yet (hand-added database entries), handle gracefully
        logger.error("portal_creation_failed", error=str(e), email=current_user["email"])
        raise HTTPException(status_code=400, detail="Não foi possível acessar o portal. Você tem uma assinatura ativa?")

@app.post("/api/payments/webhook")
async def stripe_webhook(request: Request):
    """Handle Stripe Webhooks to update user premium status."""
    payload = await request.body()
    sig_header = request.headers.get('stripe-signature')

    try:
        event = verify_webhook_signature(payload, sig_header)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

    # Handle the event
    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']
        
        # Get customer email from metadata or customer details
        metadata = session.get('metadata', {})
        email = metadata.get('email')
        
        if not email and session.get('customer_details'):
            email = session['customer_details'].get('email')
            
        if email:
            logger.info("payment_success", email=email, amount=session.get('amount_total'))
            # Ensure profile exists before updating (fix for OAuth users)
            ensure_profile_exists(email)
            success = update_user_premium(email, True)
            if success:
                logger.info("user_upgraded", email=email)
                try:
                    amount = session.get('amount_total', 2990)
                    send_payment_success_email(email, amount)
                except Exception as e:
                    logger.error("payment_email_failed", error=str(e))
            else:
                logger.error("upgrade_failed", email=email)
        else:
            logger.warning("payment_no_email", session_id=session.get('id'))
    
    # Handle subscription cancellation
    elif event['type'] == 'customer.subscription.deleted':
        subscription = event['data']['object']
        customer_id = subscription.get('customer')
        
        # Get customer email from Stripe
        try:
            import stripe
            stripe.api_key = os.getenv("STRIPE_SECRET_KEY")
            customer = stripe.Customer.retrieve(customer_id)
            email = customer.get('email')
            
            if email:
                logger.info("subscription_cancelled", email=email)
                success = update_user_premium(email, False)
                if success:
                    logger.info("user_downgraded", email=email)
                else:
                    logger.error("downgrade_failed", email=email)
        except Exception as e:
            logger.error("cancellation_handling_failed", error=str(e))
    
    # Handle subscription updates (e.g., payment failed, status change)
    elif event['type'] == 'customer.subscription.updated':
        subscription = event['data']['object']
        status = subscription.get('status')
        customer_id = subscription.get('customer')
        
        # Downgrade if subscription is no longer active
        if status in ['canceled', 'unpaid', 'past_due']:
            try:
                import stripe
                stripe.api_key = os.getenv("STRIPE_SECRET_KEY")
                customer = stripe.Customer.retrieve(customer_id)
                email = customer.get('email')
                
                if email:
                    logger.info("subscription_status_changed", email=email, status=status)
                    if status == 'canceled':
                        update_user_premium(email, False)
                        logger.info("user_downgraded_status", email=email)
            except Exception as e:
                logger.error("subscription_update_handling_failed", error=str(e))
            
    return {"status": "success"}


# ============================================
# ENDPOINTS
# ============================================

@app.get("/")
async def root():
    return {
        "name": "NorteAcoes API",
        "version": "2.0.0",
        "status": "running"
    }


@app.get("/api/stocks", response_model=List[dict])
async def get_stocks(
    # Score filters
    min_score: float = Query(0, description="Minimum super score"),
    max_score: float = Query(100, description="Maximum super score"),
    # Sector filters
    setor: Optional[str] = Query(None, description="Filter by sector"),
    subsetor: Optional[str] = Query(None, description="Filter by subsector"),
    # Valuation filters
    min_pl: Optional[float] = Query(None, description="Minimum P/L"),
    max_pl: Optional[float] = Query(None, description="Maximum P/L"),
    min_pvp: Optional[float] = Query(None, description="Minimum P/VP"),
    max_pvp: Optional[float] = Query(None, description="Maximum P/VP"),
    # Return filters
    min_dy: Optional[float] = Query(None, description="Minimum Dividend Yield"),
    min_roe: Optional[float] = Query(None, description="Minimum ROE"),
    min_roic: Optional[float] = Query(None, description="Minimum ROIC"),
    # Strategy scores
    min_graham: Optional[float] = Query(None, description="Minimum Graham Score"),
    min_greenblatt: Optional[float] = Query(None, description="Minimum Greenblatt Score"),
    min_bazin: Optional[float] = Query(None, description="Minimum Bazin Score"),
    min_qualidade: Optional[float] = Query(None, description="Minimum Quality Score"),
    # Size/Liquidity
    min_liquidity: Optional[float] = Query(None, description="Minimum liquidity (2 months)"),
    company_type: Optional[str] = Query(None, description="blue_chips, mid_caps, small_caps"),
    # Profitability
    min_margin: Optional[float] = Query(None, description="Minimum net margin"),
    min_growth: Optional[float] = Query(None, description="Minimum 5y revenue growth"),
    # Pagination
    limit: int = Query(100, description="Max results"),
    offset: int = Query(0, description="Offset for pagination"),
    sort_by: str = Query("super_score", description="Sort column"),
    order: str = Query("desc", description="Sort order (asc/desc)"),
    # Free user mode
    random_sample: bool = Query(False, description="Return random sample for free users")
):
    """Get filtered and sorted stock data with 15+ premium filters."""
    df = get_stock_data()
    
    if df.empty:
        return []
    
    # Filter by super score
    df = df[(df["super_score"] >= min_score) & (df["super_score"] <= max_score)]
    
    # Filter by sector
    if setor:
        df = df[df["setor"] == setor]
    
    # Filter by subsetor (if column exists)
    if subsetor and "subsetor" in df.columns:
        df = df[df["subsetor"] == subsetor]
    
    # P/L Range filter
    if min_pl is not None:
        df = df[df["p_l"] >= min_pl]
    if max_pl is not None:
        df = df[df["p_l"] <= max_pl]
    
    # P/VP Range filter
    if min_pvp is not None:
        df = df[df["p_vp"] >= min_pvp]
    if max_pvp is not None:
        df = df[df["p_vp"] <= max_pvp]
    
    # Dividend Yield filter
    if min_dy is not None:
        df = df[df["dividend_yield"] >= min_dy]
    
    # ROE filter
    if min_roe is not None:
        df = df[df["roe"] >= min_roe]
    
    # ROIC filter
    if min_roic is not None:
        df = df[df["roic"] >= min_roic]
    
    # Strategy score filters
    if min_graham is not None and "score_graham" in df.columns:
        df = df[df["score_graham"] >= min_graham]
    if min_greenblatt is not None and "score_greenblatt" in df.columns:
        df = df[df["score_greenblatt"] >= min_greenblatt]
    if min_bazin is not None and "score_bazin" in df.columns:
        df = df[df["score_bazin"] >= min_bazin]
    if min_qualidade is not None and "score_qualidade" in df.columns:
        df = df[df["score_qualidade"] >= min_qualidade]
    
    # Liquidity filter
    if min_liquidity is not None and "liquidez_2meses" in df.columns:
        df = df[df["liquidez_2meses"] >= min_liquidity]
    
    # Company type filter (based on price as proxy)
    if company_type:
        if company_type == "blue_chips":
            df = df[df["cotacao"] >= 30]  # Large cap proxy
        elif company_type == "mid_caps":
            df = df[(df["cotacao"] >= 10) & (df["cotacao"] < 30)]
        elif company_type == "small_caps":
            df = df[df["cotacao"] < 10]
    
    # Margin filter
    if min_margin is not None and "margem_liquida" in df.columns:
        df = df[df["margem_liquida"] >= min_margin]
    
    # Growth filter
    if min_growth is not None and "crescimento_receita_5a" in df.columns:
        df = df[df["crescimento_receita_5a"] >= min_growth]
    
    # Sort
    ascending = order.lower() == "asc"
    if sort_by in df.columns:
        df = df.sort_values(by=sort_by, ascending=ascending)
    
    # Random sample for free users (5 random from top 15)
    if random_sample:
        top_15 = df.head(15)
        if len(top_15) > 5:
            df = top_15.sample(n=5)
        else:
            df = top_15
    else:
        # Pagination
        df = df.iloc[offset:offset + limit]
    
    # Convert to dict and handle NaN
    result = df.fillna(0).to_dict(orient="records")
    
    # Enrichment: if super_score looks like a percent (> 30), it's probably 
    # a legacy record that hasn't been synced. 
    # For new records, fusion_score will be the one in the 0-100 range.
    
    return result


@app.get("/api/stocks/{ticker}")
async def get_stock(ticker: str):
    """Get single stock data by ticker."""
    df = get_stock_data()
    
    stock = df[df["papel"] == ticker.upper()]
    
    if stock.empty:
        raise HTTPException(status_code=404, detail=f"Stock {ticker} not found")
    
    return stock.fillna(0).to_dict(orient="records")[0]


@app.get("/api/stats", response_model=DashboardStats)
async def get_stats():
    """Get dashboard statistics based on Fusion Ranking (Ações Perfeitas)."""
    try:
        fusion_data = fusion.get_fusion_ranking()
    except Exception as e:
        print(f"Error getting fusion stats: {e}")
        # Fallback to empty if fusion fails
        return DashboardStats(
            total_stocks=0,
            avg_super_score=0,
            top_stock="N/A",
            top_score=0,
            sectors_count=0
        )
    
    if not fusion_data:
        return DashboardStats(
            total_stocks=0,
            avg_super_score=0,
            top_stock="N/A",
            top_score=0,
            sectors_count=0
        )
    
    # Calculate stats from Fusion Data
    total_stocks = len(fusion_data)
    scores = [s.get("fusion_score", 0) for s in fusion_data]
    avg_score = sum(scores) / len(scores) if scores else 0
    
    # Opportunities: Score > 80
    opportunities = [s for s in fusion_data if s.get("fusion_score", 0) >= 80]
    
    # Toxic: Score < 40 (Lower quality)
    toxic = [s for s in fusion_data if s.get("fusion_score", 0) < 40]
    
    # Market Sentiment: % of positive timing signals
    positive_signals = [s for s in fusion_data if s.get("timing_signal") in ["ÓTIMO", "BARGANHA"]]
    sentiment_score = (len(positive_signals) / total_stocks * 100) if total_stocks > 0 else 0
    
    if sentiment_score > 70: sentiment_str = "Muito Otimista"
    elif sentiment_score > 50: sentiment_str = "Cautelosamente Otimista"
    elif sentiment_score > 30: sentiment_str = "Neutro / Misto"
    else: sentiment_str = "Pessimista / Alerta"
    
    # Avg DY of Top 10
    top_10 = fusion_data[:10]
    # We need to get DY from the technical indicators or the row data.
    # get_fusion_ranking might not include everything by default if not specified.
    # But it has the raw data. Wait, let's check fusion.py if DY is there.
    # Looking at fusion.py view earlier, it wasn't returned in the dict.
    # Ah, I should add it to fusion.py's ranking.append if I want it here.
    
    # For now, let's get DY from the list if available, or 0.
    # Actually, let's just use the Fusion Score as a proxy or fix fusion.py first.
    
    # I'll add "dy" to the ranking in fusion.py in the next step.
    # For now, I'll assume it's there or handle fallback.
    top_dys = [s.get("dy", 0) for s in top_10]
    avg_dy = (sum(top_dys) / len(top_dys)) if top_dys else 0
    
    # New Stats (Top 10)
    top_roes = [s.get("roe", 0) for s in top_10]
    avg_roe = (sum(top_roes) / len(top_roes)) if top_roes else 0
    
    top_pls = [s.get("p_l", 0) for s in top_10 if s.get("p_l", 0) > 0] # Filter out negative P/L
    avg_pl = (sum(top_pls) / len(top_pls)) if top_pls else 0
    
    top_growths = [s.get("growth", 0) for s in top_10]
    avg_growth = (sum(top_growths) / len(top_growths)) if top_growths else 0
    
    # Best Sector (Sector with most stocks in Top 50)
    top_50 = fusion_data[:50]
    sector_counts = {}
    for s in top_50:
        sec = s.get("sector", "N/A")
        if sec != "N/A":
            sector_counts[sec] = sector_counts.get(sec, 0) + 1
    
    best_sector = max(sector_counts, key=sector_counts.get) if sector_counts else "N/A"
    
    top_stock = fusion_data[0] if fusion_data else {}
    unique_sectors = set(s.get("sector") for s in fusion_data if s.get("sector"))
    
    return DashboardStats(
        total_stocks=total_stocks,
        avg_super_score=round(avg_score, 2),
        top_stock=top_stock.get("ticker", "N/A"),
        top_score=round(top_stock.get("fusion_score", 0), 2),
        sectors_count=len(unique_sectors),
        opportunities_count=len(opportunities),
        toxic_count=len(toxic),
        market_sentiment=sentiment_str,
        avg_dividend_yield=round(avg_dy * 100, 2),
        avg_roe=round(avg_roe * 100, 2), # %
        avg_pl=round(avg_pl, 2),
        best_sector=best_sector,
        avg_growth=round(avg_growth * 100, 2) # %
    )


@app.get("/api/sectors")
async def get_sectors():
    """Get all available sectors."""
    try:
        df = get_stock_data()
        
        if df.empty or "setor" not in df.columns:
            return []
        
        # Filter out N/A and None, then get unique values
        sectors = df[df["setor"].notna() & (df["setor"] != "N/A")]["setor"].unique()
        # Convert to Python list (handles numpy types)
        sector_list = [str(s) for s in sectors if s]
        return sorted(sector_list)
    except Exception as e:
        logger.error("get_sectors_failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/strategies", response_model=List[StrategyInfo])
async def get_strategies():
    """Get all investment strategies info."""
    return [
        StrategyInfo(
            name=name,
            display_name=config["cabecalho"],
            weight=config["peso"],
            description=config["descricao"],
            filters=config["filtros"]
        )
        for name, config in ESTRATEGIAS.items()
    ]


@app.get("/api/history")
async def get_history_data(
    days: int = Query(30, description="Days to look back"),
    ticker: Optional[str] = Query(None, description="Filter by ticker")
):
    """Get historical data."""
    df = get_historico(dias=days, papel=ticker)
    
    if df.empty:
        return []
    
    return df.fillna(0).to_dict(orient="records")


@app.post("/api/history/save")
async def save_history(min_score: float = Query(8.0)):
    """Save qualified stocks to history."""
    df = get_stock_data()
    count = save_to_historico(df, score_minimo=min_score)
    return {"saved": count, "min_score": min_score}


@app.get("/api/top/{n}")
async def get_top_stocks(n: int = 10):
    """Get top N stocks by super score."""
    df = get_stock_data()
    
    if df.empty:
        return []
    
    top = df.head(n)
    return top.fillna(0).to_dict(orient="records")


# ============================================
# AI CHAT ENDPOINT (using modularized ai_chat service)
# ============================================

import re

# ============================================
# MVP SAAS FEATURES
# ============================================

# Friendly sector name mappings
FRIENDLY_SECTORS = {
    "Intermediários Financeiros": "Bancos",
    "Petróleo, Gás e Biocombustíveis": "Petróleo e Gás",
    "Exploração de Imóveis": "Imobiliário",
    "Computadores e Equipamentos": "Tecnologia",
    "Programas e Serviços": "Software",
    "Tecidos, Vestuário e Calçados": "Varejo Moda",
    "Holdings Diversificadas": "Holdings",
    "Previdência e Seguros": "Seguros",
    "Comércio e Distribuição": "Distribuição",
    "Construção e Engenharia": "Construção",
    "Serviços Financeiros Diversos": "Serviços Financeiros",
    "Máquinas e Equipamentos": "Indústria",
    "Material de Transporte": "Transporte",
    "Alimentos Processados": "Alimentos",
    "Siderurgia e Metalurgia": "Siderurgia",
}

def get_friendly_sector(sector: str) -> str:
    """Convert technical sector name to user-friendly name."""
    return FRIENDLY_SECTORS.get(sector, sector)


class PortfolioProfile(BaseModel):
    profile: str  # "conservador", "moderado", "agressivo"


@app.get("/api/chat/limits")
async def get_chat_limits(session_id: str = "anonymous"):
    """Get remaining chat limits for the session."""
    return check_chat_limit(session_id)


def _get_stock_reason(profile: str, row) -> str:
    """Generate a brief reason why this stock fits the profile."""
    ticker = row['papel']
    dy = row.get('dividend_yield', 0) * 100 if row.get('dividend_yield', 0) < 1 else row.get('dividend_yield', 0)
    roe = row.get('roe', 0) * 100 if row.get('roe', 0) < 1 else row.get('roe', 0)
    
    if profile == "conservador":
        return f"DY de {dy:.1f}% - bom pagador de dividendos"
    elif profile == "agressivo":
        return f"ROE de {roe:.1f}% - alta rentabilidade"
    else:
        return f"Score {row.get('super_score', 0):.1f} - bom equilíbrio geral"


@app.get("/api/sectors/friendly")
async def get_friendly_sectors():
    """Get list of sectors with friendly names."""
    df = get_stock_data()
    if df.empty:
        return {"sectors": []}
    
    sectors = df['setor'].unique().tolist()
    result = []
    for s in sorted(sectors):
        if s and s != 'N/A':
            result.append({
                "original": s,
                "friendly": get_friendly_sector(s),
                "count": len(df[df['setor'] == s])
            })
    
    return {"sectors": result}


@app.get("/api/stock/{ticker}/score-explain")
async def explain_stock_score(ticker: str):
    """Explain why a stock has its score - breaks down contributing factors."""
    df = get_stock_data()
    
    if df.empty:
        raise HTTPException(status_code=500, detail="Dados não disponíveis")
    
    stock = df[df['papel'] == ticker.upper()]
    if stock.empty:
        raise HTTPException(status_code=404, detail=f"Ação {ticker} não encontrada")
    
    s = stock.iloc[0]
    
    # Calculate factor contributions
    factors = []
    
    # P/L Analysis
    pl = s.get('p_l', 0)
    if pl > 0:
        if pl < 10:
            factors.append({"indicator": "P/L", "value": f"{pl:.1f}", "impact": "positive", "reason": "Muito barato - abaixo de 10"})
        elif pl < 15:
            factors.append({"indicator": "P/L", "value": f"{pl:.1f}", "impact": "positive", "reason": "Barato - abaixo de 15 (ideal Graham)"})
        elif pl < 25:
            factors.append({"indicator": "P/L", "value": f"{pl:.1f}", "impact": "neutral", "reason": "Preço justo"})
        else:
            factors.append({"indicator": "P/L", "value": f"{pl:.1f}", "impact": "negative", "reason": "Caro - acima de 25"})
    else:
        factors.append({"indicator": "P/L", "value": "Negativo", "impact": "negative", "reason": "Empresa com prejuízo"})
    
    # DY Analysis
    dy = s.get('dividend_yield', 0)
    dy_pct = dy * 100 if dy < 1 else dy
    if dy_pct >= 6:
        factors.append({"indicator": "Dividend Yield", "value": f"{dy_pct:.1f}%", "impact": "positive", "reason": "Excelente para renda passiva (>6% Bazin)"})
    elif dy_pct >= 4:
        factors.append({"indicator": "Dividend Yield", "value": f"{dy_pct:.1f}%", "impact": "positive", "reason": "Bom pagador de dividendos"})
    elif dy_pct >= 2:
        factors.append({"indicator": "Dividend Yield", "value": f"{dy_pct:.1f}%", "impact": "neutral", "reason": "Dividendos moderados"})
    else:
        factors.append({"indicator": "Dividend Yield", "value": f"{dy_pct:.1f}%", "impact": "negative", "reason": "Baixo ou sem dividendos"})
    
    # ROE Analysis
    roe = s.get('roe', 0)
    roe_pct = roe * 100 if roe < 1 else roe
    if roe_pct >= 20:
        factors.append({"indicator": "ROE", "value": f"{roe_pct:.1f}%", "impact": "positive", "reason": "Excelente rentabilidade (>20%)"})
    elif roe_pct >= 15:
        factors.append({"indicator": "ROE", "value": f"{roe_pct:.1f}%", "impact": "positive", "reason": "Boa rentabilidade (>15%)"})
    elif roe_pct >= 10:
        factors.append({"indicator": "ROE", "value": f"{roe_pct:.1f}%", "impact": "neutral", "reason": "Rentabilidade moderada"})
    else:
        factors.append({"indicator": "ROE", "value": f"{roe_pct:.1f}%", "impact": "negative", "reason": "Baixa rentabilidade"})
    
    # P/VP Analysis
    pvp = s.get('p_vp', 0)
    if pvp > 0:
        if pvp < 1:
            factors.append({"indicator": "P/VP", "value": f"{pvp:.2f}", "impact": "positive", "reason": "Negociando abaixo do valor patrimonial"})
        elif pvp < 1.5:
            factors.append({"indicator": "P/VP", "value": f"{pvp:.2f}", "impact": "positive", "reason": "Preço justo (ideal Graham <1.5)"})
        elif pvp < 3:
            factors.append({"indicator": "P/VP", "value": f"{pvp:.2f}", "impact": "neutral", "reason": "Preço normal"})
        else:
            factors.append({"indicator": "P/VP", "value": f"{pvp:.2f}", "impact": "negative", "reason": "Caro em relação ao patrimônio"})
    
    # Liquidity Analysis
    liq = s.get('liquidez_2meses', 0)
    if liq >= 100_000_000:
        factors.append({"indicator": "Liquidez", "value": f"R$ {liq/1e6:.1f}M/dia", "impact": "positive", "reason": "Alta liquidez - fácil negociar"})
    elif liq >= 10_000_000:
        factors.append({"indicator": "Liquidez", "value": f"R$ {liq/1e6:.1f}M/dia", "impact": "neutral", "reason": "Liquidez moderada"})
    elif liq >= 1_000_000:
        factors.append({"indicator": "Liquidez", "value": f"R$ {liq/1e6:.1f}M/dia", "impact": "neutral", "reason": "Liquidez baixa"})
    else:
        factors.append({"indicator": "Liquidez", "value": f"R$ {liq/1e3:.0f}K/dia", "impact": "negative", "reason": "Baixa liquidez - difícil negociar"})
    
    # Calculate positive/negative counts
    positive_count = len([f for f in factors if f["impact"] == "positive"])
    negative_count = len([f for f in factors if f["impact"] == "negative"])
    
    return {
        "ticker": ticker.upper(),
        "sector": get_friendly_sector(s.get('setor', 'N/A')),
        "super_score": round(s.get('super_score', 0), 1),
        "scores": {
            "graham": round(s.get('score_graham', 0), 1),
            "greenblatt": round(s.get('score_greenblatt', 0), 1),
            "bazin": round(s.get('score_bazin', 0), 1),
            "qualidade": round(s.get('score_qualidade', 0), 1)
        },
        "factors": factors,
        "summary": f"{positive_count} pontos positivos, {negative_count} pontos negativos",
        "recommendation": _get_score_recommendation(positive_count, negative_count, s)
    }


def _get_score_recommendation(positive: int, negative: int, stock) -> str:
    """Generate a brief recommendation based on the analysis."""
    score = stock.get('super_score', 0)
    if score >= 25:
        return "Excelente oportunidade - múltiplos indicadores favoráveis"
    elif score >= 20:
        return "Boa oportunidade - maioria dos indicadores favoráveis"
    elif score >= 15:
        return "Oportunidade moderada - alguns pontos de atenção"
    elif score >= 10:
        return "Cautela recomendada - vários pontos negativos"
    else:
        return "Alto risco - múltiplos indicadores desfavoráveis"





from fpdf import FPDF
from fastapi.responses import Response

# ============================================
# ALERT SYSTEM (ENGAGEMENT)
# ============================================

@app.get("/api/alerts")
async def get_alerts():
    """Get alerts about significant market changes."""
    current_df = get_stock_data()
    
    if current_df.empty:
        return {"alerts": []}
    
    current_top_10 = current_df.nlargest(10, 'super_score')['papel'].tolist()
    
    # Get history from 7 days ago
    try:
        from datetime import datetime, timedelta
        history_df = get_historico(dias=7)
        
        alerts = []
        
        if not history_df.empty:
            # Find closest date to 7 days ago that has data
            dates = sorted(history_df['data'].unique())
            if dates:
                oldest_date = dates[0]
                old_df = history_df[history_df['data'] == oldest_date]
                
                # Compare Top 10
                if not old_df.empty and 'super_score' in old_df.columns:
                    old_top_10 = old_df.nlargest(10, 'super_score')['papel'].tolist()
                    
                    new_entrants = set(current_top_10) - set(old_top_10)
                    dropped_out = set(old_top_10) - set(current_top_10)
                    
                    for ticker in new_entrants:
                        alerts.append({
                            "type": "success",
                            "icon": "🚀",
                            "title": "Nova Top 10!",
                            "message": f"{ticker} entrou no Top 10 nesta semana."
                        })
                        
                    for ticker in dropped_out:
                        alerts.append({
                            "type": "warning",
                            "icon": "🔻",
                            "title": "Saiu do Top 10",
                            "message": f"{ticker} saiu do ranking das 10 melhores."
                        })
    except Exception as e:
        print(f"Erro ao gerar alertas históricos: {e}")
        alerts = []
        
    # If no history alerts (or first run), generating some insights based on current data
    if not alerts:
        # High DY Alert
        high_dy = current_df[current_df['dividend_yield'] > 0.12]
        for _, row in high_dy.head(2).iterrows():
            alerts.append({
                "type": "info",
                "icon": "💰",
                "title": "Dividendos Altos",
                "message": f"{row['papel']} está pagando {(row['dividend_yield']*100):.1f}% de dividendos."
            })
            
        # Cheap Stock Alert
        cheap = current_df[(current_df['p_l'] > 0) & (current_df['p_l'] < 4)].head(2)
        for _, row in cheap.iterrows():
            alerts.append({
                "type": "info",
                "icon": "🏷️",
                "title": "Ação Barata",
                "message": f"{row['papel']} está com P/L de {row['p_l']:.1f}."
            })
            
    return {"alerts": alerts}





# ============================================
# AI CHAT - FULLY DYNAMIC (NO HARDCODED MAPPINGS)
# ============================================
# The AI interprets user intent directly from context
# including typos, synonyms, and sector correlations

@app.post("/api/chat")
async def chat_with_ai(request: ChatRequest, session_id: str = "anonymous"):
    """Dynamic AI chat - uses modularized ai_chat service."""
    df = get_stock_data()
    return process_chat(request, df, session_id)



# ============================================
# PORTFOLIO GENERATOR
# ============================================


class PortfolioRequest(BaseModel):
    profile: str

@app.post("/api/portfolio/suggested")
def get_suggested_portfolio(request: PortfolioRequest):
    """Generate suggested portfolio using Fusion Ranking (Ações Perfeitas)."""
    try:
        fusion_list = get_fusion_ranking()
        market_df = get_market_data()
        
        if not fusion_list:
            raise HTTPException(status_code=404, detail="No data available")
        
        # Create market lookup for fundamentals
        market_dict = {}
        if not market_df.empty:
            market_dict = market_df.set_index('papel').to_dict('index')
        
        # Enrich Fusion list with Market Data fundamentals
        fixed_list = []
        for item in fusion_list:
            new_item = item.copy()
            ticker = new_item.get('ticker')
            
            if ticker in market_dict:
                m_data = market_dict[ticker]
                if 'fundamentals' not in new_item:
                    new_item['fundamentals'] = {}
                else:
                    new_item['fundamentals'] = new_item['fundamentals'].copy()
                # Map extracted fields
                new_item['fundamentals']['dividend_yield'] = m_data.get('dividend_yield', 0)
                new_item['fundamentals']['p_l'] = m_data.get('p_l', 0)
                new_item['fundamentals']['p_vp'] = m_data.get('p_vp', 0)
                new_item['fundamentals']['roe'] = m_data.get('roe', 0)
                new_item['fundamentals']['liquidez_corrente'] = m_data.get('liquidez_corrente', 0)
                new_item['fundamentals']['liquidez_2meses'] = m_data.get('liquidez_2meses', 0)
                new_item['fundamentals']['div_bruta_patrimonio'] = m_data.get('div_bruta_patrimonio', 0)
            
            fixed_list.append(new_item)

        profile = request.profile.lower()
        
        criteria_desc = ""
        objective_desc = ""
        disclaimer = "Sugestões baseadas no algoritmo Fusion (Ações Perfeitas)."
        
        # Helper getters
        def get_fund(stock, key, default=0):
            return stock.get('fundamentals', {}).get(key, default) or 0

        if profile == 'conservador':
            criteria_desc = "Value Investing (Graham/Bazin) + Renda"
            objective_desc = "Segurança, Preço Justo e Dividendos"
            
            # COMPLEX CONSERVATIVE STRATEGY
            # 1. Safety: Profitable (P/L > 0)
            # 2. Valuation: Not Overvalued (P/VP < 3.0) - Margin of Safety
            # 3. Quality: Decent ROE (> 10%)
            # 4. Income: Decent Yield (> 4%)
            # 5. Liquidity: Volume > 1M (Easy to exit)
            # 6. Trend: Not a Falling Knife (Tech Prob >= 40%) - Avoid severe downtrends
            # 7. Sustainability: Payout < 120% (Avoid burning cash to pay divs)
            # 8. Leverage: Debt/Equity < 2.0 (Avoid explosive debt)
            
            filtered_list = [
                s for s in fixed_list
                if get_fund(s, 'p_l') > 0                    # Lucrativa
                and get_fund(s, 'p_vp') < 3.0                # Preço Justo/Barato
                and get_fund(s, 'roe') > 0.08                # Rentabilidade Minima
                and get_fund(s, 'dividend_yield') > 0.04     # Renda Passiva
                and get_fund(s, 'liquidez_2meses') > 1000000 # Liquidez Diária > 1M
                and s.get('tech_prob', 0) >= 0.4             # Evitar Tendência de Baixa Forte
                and (get_fund(s, 'dividend_yield') * get_fund(s, 'p_l')) <= 1.2 # Payout Sustentável
                and get_fund(s, 'div_bruta_patrimonio') < 2.0 # Alavancagem Controlada
            ]
            
            # Sorting: "Deep Value Score"
            # Prioritizes cheap assets (low P/VP) that pay well (High DY) and are quality (High Fusion)
            # Score = (Norm DY * 2) + (1/P_VP * 1) + (Fusion * 1)
            def conservative_score(x):
                dy = get_fund(x, 'dividend_yield')
                pvp = get_fund(x, 'p_vp')
                safe_pvp = pvp if pvp > 0.1 else 1 # Avoid div/0
                valuation_score = 1 / safe_pvp
                return (dy * 100) + (valuation_score * 0.5) + (x.get('fusion_score', 0) / 20)
                
            filtered_list.sort(key=conservative_score, reverse=True)
            
        elif profile == 'agressivo':
            criteria_desc = "Alta Volatilidade + Momentum + Turnaround"
            objective_desc = "Ganhos Exponenciais (Risco Elevado)"
            
            # AGGRESSIVE STRATEGY
            # Focus on Technical Breakouts (Momentum) + High Upside potential
            # Doesn't mind higher P/L if growth is there
            
            filtered_list = [
                s for s in fixed_list
                if s.get('tech_prob', 0) >= 0.7          # Strong Technical Trend (70%+)
                and get_fund(s, 'liquidez_2meses') > 500000 # Liquidez Diária > 500k
            ]
            
            # Sorting: "Momentum Score"
            # Tech Strength dominated, but tie-break with ROE (Efficiency)
            filtered_list.sort(key=lambda x: (x.get('tech_prob', 0), get_fund(x, 'roe')), reverse=True)
            
        else: # Moderado
            criteria_desc = "Ações Perfeitas (Fusion Score)"
            objective_desc = "O Melhor dos Dois Mundos (Quality/Growth)"
            
            # MODERATE STRATEGY
            # The "Perfect Stock" - High scores in both Fund and Tech
            filtered_list = [
                s for s in fixed_list
                if s.get('fusion_score', 0) >= 60        # Alta Qualidade Geral
                and s.get('matches_tech') is True        # Tecnico concorda com Fundamental
                and get_fund(s, 'liquidez_2meses') > 1000000 # Liquidez Diária > 1M
            ]
            filtered_list.sort(key=lambda x: x.get('fusion_score', 0), reverse=True)

        # Fallback Logic (if filters are too strict)
        if not filtered_list:
            if profile == 'conservador':
                 # Fallback: Just Dividend Kings (High DY + Positive P/L)
                 filtered_list = [s for s in fixed_list if get_fund(s, 'dividend_yield') > 0.04 and get_fund(s, 'p_l') > 0]
                 filtered_list.sort(key=lambda x: get_fund(x, 'dividend_yield'), reverse=True)
            elif profile == 'agressivo':
                 # Fallback: Just pure Technical Strength
                 filtered_list = sorted(fixed_list, key=lambda x: x.get('tech_prob', 0), reverse=True)
            else:
                 # Fallback: Just Top Fusion Score
                 filtered_list = sorted(fixed_list, key=lambda x: x.get('fusion_score', 0), reverse=True)
            
            # If still empty (very rare)
            if not filtered_list:
                filtered_list = sorted(fixed_list, key=lambda x: x.get('fusion_score', 0), reverse=True)

        # Select Top 5
        top_stocks = filtered_list[:5]
        
        stocks_list = []
        for s in top_stocks:
            ticker = s.get('ticker')
            fund = s.get('fundamentals', {})
            ai_verdict = s.get('ai_verdict', {})
            
            # Handle ai_verdict if it's a string (which it is in Fusion) or dict
            reason = ""
            if isinstance(ai_verdict, dict):
                 reason = ai_verdict.get('summary')
            elif isinstance(ai_verdict, str):
                 reason = f"{ai_verdict} ({s.get('ai_recommendation', '')})"
                 
            if not reason:
                 reason = f"Fusion Score: {s.get('fusion_score', 0):.1f}"
            
            stocks_list.append({
                "ticker": ticker,
                "sector": s.get('sector', 'N/A'),
                "price": s.get('price', 0),
                "super_score": s.get('fusion_score', 0),
                "p_l": fund.get('p_l', 0),
                "dividend_yield": round((fund.get('dividend_yield', 0) or 0) * 100, 2),
                "roe": round((fund.get('roe', 0) or 0) * 100, 2),
                "liquidity": fund.get('liquidez_2meses', 0), # Return Volume to UI
                "reason": reason
            })
            
        return {
            "profile": request.profile,
            "criteria": {
                "description": criteria_desc,
                "objective": objective_desc,
                "filters": "Fusion Algorithm" 
            },
            "stocks": stocks_list,
            "disclaimer": disclaimer
        }
    except Exception as e:
        logger.error("suggested_portfolio_failed", error=str(e))
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))



from services.report_service import generate_pdf_report

@app.get("/api/reports/weekly")
async def generate_weekly_report(current_user: dict = Depends(get_current_user)):
    """
    Gera um relatório PDF semanal profisisonal (v2.0) com gráficos.
    Apenas para usuários Premium.
    """
    if not current_user.get("is_premium"):
        raise HTTPException(status_code=403, detail="Apenas usuários Premium podem baixar relatórios.")

    try:
        # Get both Fusion ranking (for scores/verdict) and Market Data (for fundamentals)
        fusion_ranking = get_fusion_ranking()
        market_df = get_market_data()
        
        if not fusion_ranking or market_df.empty:
             raise HTTPException(status_code=404, detail="Dados de mercado indisponíveis")

        # Create lookup from market data by ticker
        market_dict = market_df.set_index('papel').to_dict('index')
        
        # Merge Fusion data with market fundamentals
        flat_data = []
        for item in fusion_ranking:
            ticker = item.get('ticker')
            
            # Start with market data if available (has all fundamentals)
            market_row = market_dict.get(ticker, {})
            flat = dict(market_row)  # Copy all market fields
            
            # Override with Fusion-specific fields
            flat['papel'] = ticker
            flat['cotacao'] = item.get('price', flat.get('cotacao', 0))
            flat['setor'] = item.get('sector', flat.get('setor', 'N/A'))
            flat['super_score'] = item.get('fusion_score', flat.get('super_score', 0))
            
            # AI Verdict from Fusion
            flat['ai_recommendation'] = item.get('ai_recommendation', 'NEUTRO')
            ai_verdict = item.get('ai_verdict', {})
            if isinstance(ai_verdict, dict):
                flat['ai_summary'] = ai_verdict.get('summary', '')
            else:
                flat['ai_summary'] = str(ai_verdict) if ai_verdict else ''
            
            # Ensure red_flags is a list
            if 'red_flags' not in flat or not isinstance(flat.get('red_flags'), list):
                flat['red_flags'] = []
            
            flat_data.append(flat)
            
        df = pd.DataFrame(flat_data)

        # Generate PDF using the new service
        pdf_bytes = generate_pdf_report(df)
        
        buffer = io.BytesIO(pdf_bytes)
        buffer.seek(0)
        
        filename = f"norteacoes_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        
        return StreamingResponse(
            buffer, 
            media_type="application/pdf",
            headers={
                "Content-Disposition": f"attachment; filename={filename}",
                "Cache-Control": "no-cache, no-store, must-revalidate",
                "Pragma": "no-cache",
                "Expires": "0"
            }
        )
        
    except Exception as e:
        logger.error("pdf_generation_failed", error=str(e))
        raise HTTPException(status_code=500, detail="Erro ao gerar relatório PDF")



# ============================================
# PORTFOLIO MONITOR (STOP LOSS)
# ============================================

@app.get("/api/portfolio/monitor")
async def monitor_portfolio(
    current_user: dict = Depends(get_current_user)
):
    """
    Runs the daily portfolio monitor and returns alerts (Stop Loss / Red Flags).
    Only available for authenticated users.
    """
    from core.portfolio.monitor import DailyMonitor
    
    try:
        monitor = DailyMonitor()
        alerts = monitor.run_check()
        return alerts
    except Exception as e:
        logger.error("monitor_api_error", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


# ============================================
# FULL STOCK ANALYSIS (PREMIUM MODAL v2.0)
# ============================================

def calculate_fair_value(price: float, pl: float, pvp: float, dy: float, roe: float, lpa: float = None) -> dict:
    """Calculate fair value using multiple professional methods."""
    fair_values = {}
    
    # Method 1: Graham Number (conservative)
    if pl > 0 and pvp > 0:
        vpa = price / pvp if pvp > 0 else 0
        if lpa and lpa > 0 and vpa > 0:
            graham = (22.5 * lpa * vpa) ** 0.5
            fair_values["graham"] = round(graham, 2)
    
    # Method 2: Bazin (dividend-focused) - DY should be at least 6%
    if dy > 0:
        bazin_price = (dy / 100 * price) / 0.06  # Target 6% yield
        fair_values["bazin"] = round(bazin_price, 2)
    
    # Method 3: P/L based (sector average assumption of 12)
    if pl > 0:
        lpa_estimated = price / pl
        pl_fair = lpa_estimated * 12  # Assuming fair P/L of 12
        fair_values["earnings"] = round(pl_fair, 2)
    
    # Method 4: ROE-based (Greenblatt style)
    if roe > 0 and pvp > 0:
        vpa = price / pvp
        expected_earnings = vpa * (roe / 100)
        roe_fair = expected_earnings * 10  # 10x earnings
        fair_values["roe_based"] = round(roe_fair, 2)
    
    # Calculate average fair value
    if fair_values:
        avg_fair = sum(fair_values.values()) / len(fair_values)
        fair_values["average"] = round(avg_fair, 2)
        fair_values["upside"] = round(((avg_fair / price) - 1) * 100, 1) if price > 0 else 0
    
    return fair_values


def generate_ai_verdict(stock_data: dict, tech_data: dict) -> dict:
    """Generate professional AI-powered verdict and recommendation."""
    score = stock_data.get('super_score', 0)
    pl = stock_data.get('p_l', 0)
    dy = stock_data.get('dividend_yield', 0)
    roe = stock_data.get('roe', 0)
    pvp = stock_data.get('p_vp', 0)
    liq = stock_data.get('liquidez_2meses') or stock_data.get('volume') or 0
    debt_equity = stock_data.get('div_bruta_patrimonio', 0) or 0
    
    # Technical signals
    tech_signal = tech_data.get('summary_signal', 'NEUTRAL')
    oscillators = tech_data.get('oscillators', {})
    ma_signal = tech_data.get('moving_averages', {}).get('RECOMMENDATION', 'NEUTRAL')
    
    # Scoring system
    fund_points = 0
    tech_points = 0
    highlights = []
    concerns = []
    
    # --- RISK CHECKS (BLIND SPOTS) ---
    risk_level = "NONE"
    
    # 1. Liquidity Risk
    if liq < 500_000:
        concerns.append(f"Baixa Liquidez (Vol ~{liq/1000:.0f}k)")
        risk_level = "CRITICAL"
        
    # 2. Payout Sustainability
    payout = dy * pl
    if payout > 1.2 and dy > 0.10:
        concerns.append(f"Payout Insustentável ({payout*100:.0f}%)")
        risk_level = "HIGH" if risk_level != "CRITICAL" else risk_level
        
    # 3. Debt Risk
    if debt_equity > 2.0:
        concerns.append(f"Alavancagem Alta ({debt_equity:.1f}x)")
        risk_level = "HIGH" if risk_level != "CRITICAL" else risk_level

    # Fundamental scoring
    if pl > 0 and pl < 10:
        fund_points += 3
        highlights.append("P/L muito atrativo")
    elif pl > 0 and pl < 15:
        fund_points += 2
        highlights.append("Valuation interessante")
    elif pl > 25 or pl < 0:
        fund_points -= 2
        concerns.append("Valuation esticado ou prejuízo")
    
    dy_pct = dy * 100 if dy < 1 else dy
    if dy_pct >= 6:
        fund_points += 3
        highlights.append(f"Dividendo excepcional ({dy_pct:.1f}%)")
    elif dy_pct >= 4:
        fund_points += 2
        highlights.append("Bom pagador de dividendos")
    elif dy_pct < 1:
        concerns.append("Sem dividendos relevantes")
    
    roe_pct = roe * 100 if roe < 1 else roe
    if roe_pct >= 20:
        fund_points += 3
        highlights.append(f"ROE excepcional ({roe_pct:.1f}%)")
    elif roe_pct >= 15:
        fund_points += 2
        highlights.append("Boa rentabilidade")
    elif roe_pct < 10:
        fund_points -= 1
        concerns.append("Rentabilidade baixa")
    
    if pvp > 0 and pvp < 1:
        fund_points += 2
        highlights.append("Negociando abaixo do patrimônio")
    elif pvp > 3:
        concerns.append("P/VP elevado")
    
    # Technical scoring
    if 'STRONG_BUY' in tech_signal:
        tech_points += 3
        highlights.append("Forte sinal técnico de compra")
    elif 'BUY' in tech_signal:
        tech_points += 2
    elif 'STRONG_SELL' in tech_signal:
        tech_points -= 3
        concerns.append("Sinal técnico de venda forte")
    elif 'SELL' in tech_signal:
        tech_points -= 2
        concerns.append("Pressão vendedora")
    
    if 'STRONG_BUY' in str(ma_signal):
        tech_points += 2
        highlights.append("Médias móveis favoráveis")
    elif 'STRONG_SELL' in str(ma_signal):
        tech_points -= 2
    
    # Final verdict
    total_points = fund_points + tech_points
    
    # Override based on Risk Level
    if risk_level == "CRITICAL":
        verdict = "RISCO CRÍTICO"
        verdict_color = "red"
        verdict_icon = "☠️"
        recommendation = "EVITAR/VENDA"
        summary = "Ativo apresenta riscos estruturais graves (Liquidez ou Solvência). Não recomendado."
        total_points = -10 # Reset score
    elif risk_level == "HIGH":
        verdict = "ALTO RISCO"
        verdict_color = "orange"
        verdict_icon = "⚠️"
        recommendation = "CAUTELA"
        summary = "Indicadores fundamentalistas ou de sustentabilidade preocupantes. Exige análise detalhada."
        total_points = -5
    elif total_points >= 8:
        verdict = "OPORTUNIDADE EXCEPCIONAL"
        verdict_color = "emerald"
        verdict_icon = "🏆"
        recommendation = "COMPRA FORTE"
        summary = "Ativo apresenta combinação rara de fundamentos sólidos com timing técnico favorável. Considerar posição significativa."
    elif total_points >= 5:
        verdict = "MUITO ATRATIVO"
        verdict_color = "green"
        verdict_icon = "✨"
        recommendation = "COMPRA"
        summary = "Fundamentos consistentes sustentam a tese de investimento. O momento técnico sugere boa entrada."
    elif total_points >= 2:
        verdict = "ATRATIVO"
        verdict_color = "cyan"
        verdict_icon = "👍"
        recommendation = "COMPRA MODERADA"
        summary = "Ativo com métricas interessantes. Avaliar se encaixa no perfil da carteira."
    elif total_points >= -1:
        verdict = "NEUTRO"
        verdict_color = "slate"
        verdict_icon = "➖"
        recommendation = "MANTER/AGUARDAR"
        summary = "Sem catalisadores claros no momento. Aguardar melhor ponto de entrada."
    elif total_points >= -4:
        verdict = "CAUTELA"
        verdict_color = "amber"
        verdict_icon = "⚠️"
        recommendation = "EVITAR"
        summary = "Indicadores mistos sugerem cautela. Há opções melhores no mercado."
    else:
        verdict = "RISCO ELEVADO"
        verdict_color = "red"
        verdict_icon = "🚨"
        recommendation = "VENDA/EVITAR"
        summary = "Múltiplos sinais de alerta. Considerar reduzir exposição se já posicionado."
    
    return {
        "verdict": verdict,
        "verdict_color": verdict_color,
        "verdict_icon": verdict_icon,
        "recommendation": recommendation,
        "summary": summary,
        "fund_score": fund_points,
        "tech_score": tech_points,
        "total_score": total_points,
        "highlights": highlights[:4],  # Top 4
        "concerns": concerns[:3]  # Top 3
    }


def get_sector_ranking(df, ticker: str, sector: str) -> dict:
    """Calculate stock's ranking within its sector."""
    sector_stocks = df[df['setor'] == sector]
    if sector_stocks.empty:
        return {"rank": 0, "total": 0, "percentile": 0}
    
    sector_sorted = sector_stocks.sort_values('super_score', ascending=False)
    rank = sector_sorted['papel'].tolist().index(ticker) + 1 if ticker in sector_sorted['papel'].values else 0
    total = len(sector_sorted)
    percentile = round((1 - (rank / total)) * 100) if total > 0 else 0
    
    # Top performers in sector
    top_3 = sector_sorted.head(3)[['papel', 'super_score']].to_dict('records')
    
    return {
        "rank": rank,
        "total": total,
        "percentile": percentile,
        "top_3": top_3
    }


@app.get("/api/stock/{ticker}/full-analysis")
async def get_full_stock_analysis(ticker: str):
    """
    Returns comprehensive PREMIUM analysis for detail modal.
    v2.0: AI Verdict, Fair Value, Sector Comparison, Risk Metrics
    """
    import json
    from pathlib import Path
    import traceback
    
    ticker = ticker.upper()
    
    try:
        df = get_stock_data()
        
        if df.empty:
            raise HTTPException(status_code=500, detail="Dados não disponíveis")
        
        stock = df[df['papel'] == ticker]
        if stock.empty:
            raise HTTPException(status_code=404, detail=f"Ação {ticker} não encontrada")
        
        s = stock.iloc[0]
    
        # Load technical data from cache
        tech_cache_path = Path(__file__).parent.parent / "data" / "technical_scores_cache.json"
        tech_data = {}
        try:
            if tech_cache_path.exists():
                with open(tech_cache_path, 'r', encoding='utf-8') as f:
                    cache = json.load(f)
                    tech_data = cache.get('data', {}).get(ticker, {})
        except Exception as e:
            logger.warning("tech_cache_load_error", ticker=ticker, error=str(e))
    
        indicators = tech_data.get('indicators', {})
        oscillators = tech_data.get('oscillators', {})
        moving_averages = tech_data.get('moving_averages', {})
        
        # Base metrics (handle NaN/None safely)
        price = float(s.get('cotacao') or 0)
        dy = s.get('dividend_yield') or 0
        dy_pct = (dy * 100 if dy < 1 else dy) if dy else 0
        roe = s.get('roe') or 0
        roe_pct = (roe * 100 if roe < 1 else roe) if roe else 0
        roic = s.get('roic') or 0
        roic_pct = (roic * 100 if roic < 1 else roic) if roic else 0
        margem = s.get('margem_liquida') or 0
        margem_pct = (margem * 100 if margem < 1 else margem) if margem else 0
        pl = float(s.get('p_l') or 0)
        pvp = float(s.get('p_vp') or 0)
        
        # Technical indicators
        rsi = indicators.get('RSI')
        ema200 = indicators.get('EMA200')
        close = indicators.get('close') or price
        change = indicators.get('change') or 0
        volume = indicators.get('volume') or 0
        
        # PREMIUM: AI Verdict
        ai_verdict = generate_ai_verdict(s.to_dict(), tech_data)
    
        # PREMIUM: Fair Value Calculation
        fair_value = calculate_fair_value(price, pl, pvp, dy_pct, roe_pct)
        
        # PREMIUM: Sector Ranking
        sector = s.get('setor', 'N/A')
        sector_ranking = get_sector_ranking(df, ticker, sector)
        
        # Fundamental section
        fundamental = {
            "p_l": round(pl or 0, 2),
            "p_vp": round(pvp or 0, 2),
            "dividend_yield": round(dy_pct or 0, 2),
            "roe": round(roe_pct or 0, 2),
            "roic": round(roic_pct or 0, 2),
            "margem_liquida": round(margem_pct or 0, 2),
            "liquidez_corrente": round(float(s.get('liquidez_corrente') or 0), 2),
            "div_bruta_patrimonio": round(float(s.get('div_bruta_patrimonio') or 0), 2),
            "lpa": round(float(s.get('lpa') or 0), 2),
            "vpa": round(float(s.get('vpa') or 0), 2),
            "scores": {
                "super_score": round(float(s.get('super_score') or 0), 1),
                "graham": round(float(s.get('score_graham') or 0), 1),
                "greenblatt": round(float(s.get('score_greenblatt') or 0), 1),
                "bazin": round(float(s.get('score_bazin') or 0), 1),
                "qualidade": round(float(s.get('score_qualidade') or 0), 1)
            }
        }
        
        # Technical section
        technical = {
            "summary": tech_data.get('summary_signal', 'NEUTRAL'),
            "summary_score": tech_data.get('summary_score', 0.5),
            "oscillators": {
                "signal": oscillators.get('RECOMMENDATION', 'NEUTRAL'),
                "buy": oscillators.get('BUY', 0),
                "sell": oscillators.get('SELL', 0),
                "neutral": oscillators.get('NEUTRAL', 0),
                "details": oscillators.get('COMPUTE', {})
            },
            "moving_averages": {
                "signal": moving_averages.get('RECOMMENDATION', 'NEUTRAL'),
                "buy": moving_averages.get('BUY', 0),
                "sell": moving_averages.get('SELL', 0),
                "neutral": moving_averages.get('NEUTRAL', 0),
                "details": moving_averages.get('COMPUTE', {})
            },
            "indicators": {
                "rsi": round(rsi, 1) if rsi else None,
                "macd": {
                    "value": round(indicators.get('MACD.macd') or 0, 3),
                    "signal": round(indicators.get('MACD.signal') or 0, 3),
                    "histogram": round((indicators.get('MACD.macd') or 0) - (indicators.get('MACD.signal') or 0), 3)
                },
                "stochastic": {
                    "k": round(indicators.get('Stoch.K') or 0, 1),
                    "d": round(indicators.get('Stoch.D') or 0, 1)
                },
                "adx": round(indicators.get('ADX') or 0, 1),
                "cci": round(indicators.get('CCI20') or 0, 1),
                "momentum": round(indicators.get('Mom') or 0, 2),
                "ao": round(indicators.get('AO') or 0, 2),
                "bollinger": {
                    "upper": round(indicators.get('BB.upper') or 0, 2),
                    "lower": round(indicators.get('BB.lower') or 0, 2),
                    "middle": round(((indicators.get('BB.upper') or 0) + (indicators.get('BB.lower') or 0)) / 2, 2),
                    "width": round((indicators.get('BB.upper') or 0) - (indicators.get('BB.lower') or 0), 2)
                },
                "ema200": round(ema200, 2) if ema200 else None,
                "sma200": round(indicators.get('SMA200') or 0, 2),
                "ema50": round(indicators.get('EMA50') or 0, 2),
                "sma50": round(indicators.get('SMA50') or 0, 2),
                "ema20": round(indicators.get('EMA20') or 0, 2),
                "vwma": round(indicators.get('VWMA') or 0, 2),
                "volume": volume,
                "change": round(change or 0, 2)
            },
            "pivots": {
                "classic": {
                    "s3": round(indicators.get('Pivot.M.Classic.S3') or 0, 2),
                    "s2": round(indicators.get('Pivot.M.Classic.S2') or 0, 2),
                    "s1": round(indicators.get('Pivot.M.Classic.S1') or 0, 2),
                    "pivot": round(indicators.get('Pivot.M.Classic.Middle') or 0, 2),
                    "r1": round(indicators.get('Pivot.M.Classic.R1') or 0, 2),
                    "r2": round(indicators.get('Pivot.M.Classic.R2') or 0, 2),
                    "r3": round(indicators.get('Pivot.M.Classic.R3') or 0, 2)
                },
                "fibonacci": {
                    "s1": round(indicators.get('Pivot.M.Fibonacci.S1') or 0, 2),
                    "r1": round(indicators.get('Pivot.M.Fibonacci.R1') or 0, 2)
                }
            }
        }
        
        # Timing analysis
        above_ema200 = (close > ema200) if ema200 and close else None
        rsi_zone = "neutral"
        timing_signal = "NEUTRO"
        timing_emoji = "⚪"
        
        if rsi:
            if rsi > 70:
                rsi_zone = "overbought"
            elif rsi < 30:
                rsi_zone = "oversold"
        
        if rsi and ema200 and close:
            if rsi < 30 and close > ema200:
                timing_signal = "ÓTIMO"
                timing_emoji = "🟢"
            elif rsi < 40 and close < ema200:
                timing_signal = "BARGANHA"
                timing_emoji = "🟡"
            elif rsi > 70 and close > ema200:
                timing_signal = "ESTICADO"
                timing_emoji = "🟠"
            elif rsi > 70 and close < ema200:
                timing_signal = "PERIGO"
                timing_emoji = "🔴"
        
        timing = {
            "signal": timing_signal,
            "emoji": timing_emoji,
            "above_ema200": above_ema200,
            "rsi_zone": rsi_zone,
            "distance_to_ema200": round(((close / ema200) - 1) * 100, 2) if ema200 and close else None
        }
        
        return {
            "ticker": ticker,
            "company_name": s.get('empresa') or s.get('Empresa', 'N/A'),
            "sector": get_friendly_sector(sector),
            "subsetor": s.get('subsetor', 'N/A'),
            "price": round(price or 0, 2),
            "change": round(change or 0, 2),
            "volume": volume or 0,
            
            # PREMIUM FEATURES
            "ai_verdict": ai_verdict,
            "fair_value": fair_value,
            "sector_ranking": sector_ranking,
            
            # Standard sections
            "fundamental": fundamental,
            "technical": technical,
            "timing": timing,
            
            "updated_at": tech_data.get('updated_at') if tech_data else None
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error("full_analysis_error", ticker=ticker, error=str(e), traceback=traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Erro ao processar {ticker}: {str(e)}")


@app.get("/api/fusion/ranking")
async def get_fusion_ranking_endpoint():
    """
    Returns the 'Perfect Stock' ranking (Fusion of Fundamental + Technical Analysis).
    """
    try:
        # Move import inside try block to catch ModuleNotFoundError or Path issues
        from core.integration.fusion import get_fusion_ranking
        ranking = get_fusion_ranking()
        return ranking
    except Exception as e:
        logger.error("fusion_ranking_failed", error=str(e))
        # Return empty list on failure to avoid Frontend crash
        return []


if __name__ == "__main__":

    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)


