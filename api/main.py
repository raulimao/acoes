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



@app.post("/api/admin/refresh-cache")
async def force_refresh(background_tasks: BackgroundTasks, key: str = Query(None)):
    """Force background data update (Admin)."""
    if key != os.getenv("ADMIN_KEY", "admin123"):
        raise HTTPException(status_code=403, detail="Forbidden")
        
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
    background_tasks.add_task(update_market_data_background)
    return {"status": "success", "message": "Cron job started"}



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
    """Get dashboard statistics."""
    df = get_stock_data()
    
    if df.empty:
        return DashboardStats(
            total_stocks=0,
            avg_super_score=0,
            top_stock="N/A",
            top_score=0,
            sectors_count=0
        )
    
    return DashboardStats(
        total_stocks=len(df),
        avg_super_score=round(df["super_score"].mean(), 2),
        top_stock=df.iloc[0]["papel"],
        top_score=round(df.iloc[0]["super_score"], 2),
        sectors_count=df["setor"].nunique() if "setor" in df.columns else 0
    )


@app.get("/api/sectors")
async def get_sectors():
    """Get all available sectors."""
    df = get_stock_data()
    
    if "setor" not in df.columns:
        return []
    
    sectors = df[df["setor"] != "N/A"]["setor"].unique().tolist()
    return sorted(sectors)


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



@app.post("/api/portfolio/suggested")
async def get_suggested_portfolio(request: PortfolioProfile):
    """Get a suggested portfolio based on investor profile."""
    df = get_stock_data()
    
    if df.empty:
        raise HTTPException(status_code=500, detail="Dados não disponíveis")
    
    profile = request.profile.lower()
    
    # Define criteria for each profile
    if profile == "conservador":
        # Focus on high dividend yield, low volatility, large cap (high liquidity)
        criteria = {
            "description": "Foco em dividendos e empresas sólidas",
            "objective": "Renda passiva com baixo risco",
            "filters": "DY > 4%, P/L positivo, Alta liquidez"
        }
        # Filter: high DY, positive P/L, high liquidity
        filtered = df[
            (df['dividend_yield'] > 0.04) & 
            (df['p_l'] > 0) & 
            (df['p_l'] < 20) &
            (df['liquidez_2meses'] > 10_000_000)
        ].nlargest(5, 'dividend_yield')
        
    elif profile == "agressivo":
        # Focus on growth: high ROE, high ROIC, lower P/L
        criteria = {
            "description": "Foco em crescimento e valorização",
            "objective": "Máximo retorno aceitando mais risco",
            "filters": "ROE > 15%, ROIC > 15%, Bom score Greenblatt"
        }
        filtered = df[
            (df['roe'] > 0.15) & 
            (df['roic'] > 0.15) &
            (df['p_l'] > 0) &
            (df['liquidez_2meses'] > 1_000_000)
        ].nlargest(5, 'score_greenblatt')
        
    else:  # moderado (default)
        # Balanced approach: good overall score, decent dividend, reasonable valuation
        criteria = {
            "description": "Equilíbrio entre valor, dividendos e crescimento",
            "objective": "Crescimento sustentável com alguma renda",
            "filters": "Super Score Top 50, DY > 2%, Liquidez razoável"
        }
        filtered = df[
            (df['dividend_yield'] > 0.02) &
            (df['p_l'] > 0) &
            (df['liquidez_2meses'] > 5_000_000)
        ].nlargest(5, 'super_score')
    
    # Build response
    stocks = []
    for _, row in filtered.iterrows():
        dy = row.get('dividend_yield', 0) * 100 if row.get('dividend_yield', 0) < 1 else row.get('dividend_yield', 0)
        roe = row.get('roe', 0) * 100 if row.get('roe', 0) < 1 else row.get('roe', 0)
        
        stocks.append({
            "ticker": row['papel'],
            "sector": get_friendly_sector(row.get('setor', 'N/A')),
            "price": round(row.get('cotacao', 0), 2),
            "super_score": round(row.get('super_score', 0), 1),
            "p_l": round(row.get('p_l', 0), 1),
            "dividend_yield": round(dy, 1),
            "roe": round(roe, 1),
            "liquidity": int(row.get('liquidez_2meses', 0)),
            "reason": _get_stock_reason(profile, row)
        })
    
    return {
        "profile": profile.capitalize(),
        "criteria": criteria,
        "stocks": stocks,
        "disclaimer": "Esta é uma sugestão educacional, não uma recomendação de investimento."
    }


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
    df = get_stock_data()
    
    if df.empty:
        raise HTTPException(status_code=404, detail="No data available")

    profile = request.profile.lower()
    
    # Default values
    filtered = df.copy()
    criteria_desc = ""
    objective_desc = ""
    disclaimer = ""
    
    if profile == 'conservador':
        # High Dividend, Established Companies
        # Filter: DY > 6%, Liquidity > 1M, Positive P/L
        filtered = filtered[
            (filtered['dividend_yield'] > 6) & 
            (filtered['liquidez_2meses'] > 1000000) &
            (filtered['p_l'] > 0)
        ].sort_values(by='dividend_yield', ascending=False)
        
        criteria_desc = "Dividendos > 6% + Alta Liquidez"
        objective_desc = "Maximizar renda passiva com segurança."
        disclaimer = "Foco em empresas consolidadas pagadoras de proventos."
        
    elif profile == 'agressivo':
        # High Growth/Potential
        # Filter: Small Caps (Price < 20?), High ROE? Or just Greenblatt Score?
        # Let's use Greenblatt Score for quality + undervalue
        filtered = filtered.sort_values(by='score_greenblatt', ascending=False)
        
        criteria_desc = "Top Fórmula Mágica (Greenblatt)"
        objective_desc = "Buscar assimetrias de valor e crescimento acelerado."
        disclaimer = "Maior volatilidade esperada em busca de maiores retornos."
        
    else: # Moderado (Default)
        # Balanced Approach (Super Score)
        filtered = filtered.sort_values(by='super_score', ascending=False)
        
        criteria_desc = "Top Super Score (Multifator)"
        objective_desc = "Equilíbrio entre qualidade, preço e dividendos."
        disclaimer = "Carteira balanceada selecionada pelo algoritmo proprietário."

    # Take top 5
    top_5 = filtered.head(5)
    
    # Format for frontend
    stocks_list = []
    for _, row in top_5.iterrows():
        reason_text = ""
        if profile == 'conservador':
            reason_text = f"Alto DY de {row['dividend_yield']:.2f}%"
        elif profile == 'agressivo':
            reason_text = f"Score Greenblatt: {row.get('score_greenblatt', 0):.1f}"
        else:
            reason_text = f"Super Score: {row['super_score']:.1f}"
            
        stocks_list.append({
            "ticker": safe_str(row['papel']),
            "sector": safe_str(row.get('setor', 'N/A')),
            "price": row['cotacao'],
            "super_score": row['super_score'],
            "p_l": row['p_l'],
            "dividend_yield": row['dividend_yield'],
            "roe": row['roe'],
            "liquidity": row.get('liquidez_2meses', 0),
            "reason": reason_text
        })
        
    return {
        "profile": profile,
        "criteria": {
            "description": criteria_desc,
            "objective": objective_desc,
            "filters": "Algoritmo Proprietário" 
        },
        "stocks": stocks_list,
        "disclaimer": disclaimer
    }



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
        df = get_stock_data()
        if df.empty:
            raise HTTPException(status_code=404, detail="Dados de mercado indisponíveis")

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


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)


