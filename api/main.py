"""
FastAPI Backend for TopAções Dashboard
Serves stock data, strategies, and history via REST API
"""
import sys
from pathlib import Path

# Load environment variables from .env file
from dotenv import load_dotenv
load_dotenv()

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from fastapi import FastAPI, HTTPException, Query, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
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
from services.setores_service import get_all_setores

from services.auth_service import add_user, verify_user, get_user_by_email, initialize_database, update_user_premium, upsert_oauth_user
from services.payment_service import create_checkout_session, verify_webhook_signature, create_portal_session
from services.email_service import send_welcome_email, send_payment_success_email
from fastapi import FastAPI, HTTPException, Query, Depends, Request
from fastapi.responses import StreamingResponse
from config.strategies_config import ESTRATEGIAS, FILTROS
from fpdf import FPDF
import io

# JWT Configuration
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "topacoes-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7  # 7 days

security = HTTPBearer(auto_error=False)

# Initialize database on startup
initialize_database()

app = FastAPI(
    title="TopAções API",
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

# Cache for stock data
_cached_data = None
_cache_time = None
CACHE_DURATION = 300  # 5 minutes


def get_stock_data():
    """Get stock data with caching."""
    global _cached_data, _cache_time
    
    now = datetime.now()
    if _cached_data is not None and _cache_time is not None:
        if (now - _cache_time).seconds < CACHE_DURATION:
            return _cached_data
    
    _cached_data = carregar_dados_completos()
    _cache_time = now
    return _cached_data


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
    name: str
    email: str
    password: str


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

@app.post("/api/auth/login", response_model=TokenResponse)
async def login(request: LoginRequest):
    """Authenticate user and return JWT token."""
    user = verify_user(request.email, request.password)
    
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
    # Check if user already exists
    existing = get_user_by_email(request.email)
    if existing:
        raise HTTPException(status_code=400, detail="Email já cadastrado")
    
    # Create username from email
    username = request.email.split("@")[0]
    
    # Add user to database (default is_premium=False)
    success = add_user(username, request.name, request.email, request.password)
    if not success:
        raise HTTPException(status_code=400, detail="Erro ao criar usuário")
    
    # Create token
    access_token = create_access_token(
        data={"sub": request.email, "name": request.name}
    )
    
    return TokenResponse(
        access_token=access_token,
        user={"username": username, "name": request.name, "email": request.email, "is_premium": False}
    )

    # Convert to background task in production to not block response
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
            
    return {"status": "success"}


# ============================================
# ENDPOINTS
# ============================================

@app.get("/")
async def root():
    return {
        "name": "TopAções API",
        "version": "2.0.0",
        "status": "running"
    }


@app.get("/api/stocks", response_model=List[dict])
async def get_stocks(
    min_score: float = Query(0, description="Minimum super score"),
    max_score: float = Query(100, description="Maximum super score"),
    setor: Optional[str] = Query(None, description="Filter by sector"),
    limit: int = Query(100, description="Max results"),
    sort_by: str = Query("super_score", description="Sort column"),
    order: str = Query("desc", description="Sort order (asc/desc)")
):
    """Get filtered and sorted stock data."""
    df = get_stock_data()
    
    if df.empty:
        return []
    
    # Filter by score
    df = df[(df["super_score"] >= min_score) & (df["super_score"] <= max_score)]
    
    # Filter by sector
    if setor:
        df = df[df["setor"] == setor]
    
    # Sort
    ascending = order.lower() == "asc"
    if sort_by in df.columns:
        df = df.sort_values(by=sort_by, ascending=ascending)
    
    # Limit
    df = df.head(limit)
    
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
# AI CHAT ENDPOINT
# ============================================

class ChatMessage(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    message: str
    history: Optional[List[ChatMessage]] = []

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

# Chat limits storage (in production, use Redis or database)
chat_limits = {}  # {session_id: {"count": 0, "date": "2024-01-01"}}
FREE_CHAT_LIMIT = 5

def check_chat_limit(session_id: str = "anonymous") -> dict:
    """Check if user has remaining free chats."""
    today = datetime.now().strftime("%Y-%m-%d")
    
    if session_id not in chat_limits:
        chat_limits[session_id] = {"count": 0, "date": today}
    
    # Reset count if new day
    if chat_limits[session_id]["date"] != today:
        chat_limits[session_id] = {"count": 0, "date": today}
    
    remaining = FREE_CHAT_LIMIT - chat_limits[session_id]["count"]
    return {
        "remaining": max(0, remaining),
        "limit": FREE_CHAT_LIMIT,
        "used": chat_limits[session_id]["count"],
        "can_chat": remaining > 0
    }

def increment_chat_count(session_id: str = "anonymous"):
    """Increment chat count for session."""
    today = datetime.now().strftime("%Y-%m-%d")
    if session_id not in chat_limits:
        chat_limits[session_id] = {"count": 0, "date": today}
    chat_limits[session_id]["count"] += 1


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
# PDF REPORT GENERATOR
# ============================================

@app.get("/api/reports/weekly")
async def generate_weekly_report():
    """Generate a weekly PDF report with top stocks."""
    df = get_stock_data()
    
    if df.empty:
        raise HTTPException(status_code=500, detail="Dados não disponíveis")
        
    top_10 = df.nlargest(10, 'super_score')
    
    def safe_str(text):
        """Clean string for Latin-1 encoding."""
        if not isinstance(text, str):
            text = str(text)
        # Normalize and replace common problematic chars
        replacements = {
            'ã': 'a', 'á': 'a', 'à': 'a', 'â': 'a',
            'é': 'e', 'ê': 'e',
            'í': 'i',
            'ó': 'o', 'ô': 'o', 'õ': 'o',
            'ú': 'u',
            'ç': 'c',
            'Ã': 'A', 'Á': 'A', 'À': 'A', 'Â': 'A',
            'É': 'E', 'Ê': 'E',
            'Í': 'I',
            'Ó': 'O', 'Ô': 'O', 'Õ': 'O',
            'Ú': 'U',
            'Ç': 'C',
            'R$': 'R$',  # R$ usually works in latin-1 but check
            '°': 'o',
            'º': 'o',
            'ª': 'a',
        }
        for k, v in replacements.items():
            text = text.replace(k, v)
        return text.encode('latin-1', 'ignore').decode('latin-1')

    class PDF(FPDF):
        def header(self):
            self.set_font('Arial', 'B', 15)
            self.cell(0, 10, 'TopAcoes - Relatorio Semanal', 0, 1, 'C')
            self.ln(5)
            
        def footer(self):
            self.set_font('Arial', 'I', 8)
            self.set_y(-15)
            self.cell(0, 10, f'Pagina {self.page_no()}', 0, 0, 'C')
            
    pdf = PDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    
    # Title
    pdf.set_font("Arial", "B", 16)
    pdf.cell(0, 10, f"Resumo do Mercado - {datetime.now().strftime('%d/%m/%Y')}", 0, 1)
    pdf.ln(5)
    
    # Top 10 Table
    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 10, safe_str("🏆 Top 10 Ações por Super Score:"), 0, 1)
    
    pdf.set_font("Arial", size=10)
    # Header
    pdf.cell(30, 10, "Papel", 1)
    pdf.cell(50, 10, "Setor", 1)
    pdf.cell(30, 10, safe_str("Preço"), 1)
    pdf.cell(30, 10, "Score", 1)
    pdf.cell(30, 10, "DY", 1)
    pdf.ln()
    
    # Rows
    for _, row in top_10.iterrows():
        pdf.cell(30, 10, safe_str(row['papel']), 1)
        # Truncate sector to fit
        sector = safe_str(str(row.get('setor', 'N/A')))[:20]
        pdf.cell(50, 10, sector, 1)
        pdf.cell(30, 10, f"R$ {row['cotacao']:.2f}", 1)
        pdf.cell(30, 10, f"{row['super_score']:.1f}", 1)
        dy = row['dividend_yield'] * 100 if row['dividend_yield'] < 1 else row['dividend_yield']
        pdf.cell(30, 10, f"{dy:.1f}%", 1)
        pdf.ln()
        
    pdf.ln(10)
    
    # Suggested Portfolios
    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 10, safe_str("💼 Carteiras Sugeridas:"), 0, 1)
    pdf.set_font("Arial", size=10)
    
    # Conservative
    pdf.set_text_color(0, 100, 0)
    pdf.cell(0, 10, safe_str("Conservador (Foco em Dividendos):"), 0, 1)
    pdf.set_text_color(0, 0, 0)
    conserv_stocks = df[(df['dividend_yield'] > 0.06)].nlargest(5, 'liquidez_2meses')['papel'].tolist()
    pdf.multi_cell(0, 10, ", ".join([safe_str(s) for s in conserv_stocks]))
    
    # Aggressive
    pdf.set_text_color(150, 0, 0)
    pdf.cell(0, 10, safe_str("Agressivo (Foco em Crescimento):"), 0, 1)
    pdf.set_text_color(0, 0, 0)
    aggr_stocks = df.nlargest(5, 'score_greenblatt')['papel'].tolist()
    pdf.multi_cell(0, 10, ", ".join([safe_str(s) for s in aggr_stocks]))
    
    pdf.ln(10)
    pdf.set_font("Arial", "I", 8)
    pdf.multi_cell(0, 10, safe_str("Disclaimer: Este relatório é gerado automaticamente por inteligência artificial e não constitui recomendação de compra ou venda. Invista com responsabilidade."))
    
    # Output
    return Response(content=pdf.output(dest='S').encode('latin-1'), media_type="application/pdf", headers={"Content-Disposition": "attachment; filename=relatorio_semanal.pdf"})


# ============================================
# AI CHAT - FULLY DYNAMIC (NO HARDCODED MAPPINGS)
# ============================================
# The AI interprets user intent directly from context
# including typos, synonyms, and sector correlations

def simple_fallback_response(df) -> dict:
    """Simple fallback when Groq API fails."""
    if df.empty:
        return {"response": "Desculpe, não há dados disponíveis no momento."}
    
    top_5 = df.head(5)[['papel', 'setor', 'super_score']].to_dict(orient='records')
    response = "🏆 **Top 5 ações por Super Score:**\n\n"
    for i, s in enumerate(top_5, 1):
        response += f"{i}. **{s['papel']}** ({s['setor']}) - Score: {s['super_score']:.1f}\n"
    response += "\n💡 Para análises mais detalhadas, verifique se a API Groq está configurada."
    return {"response": response}


@app.post("/api/chat")
async def chat_with_ai(request: ChatRequest, session_id: str = "anonymous"):
    """Dynamic AI chat - lets Groq interpret user intent with full database context."""
    import os
    
    # Check chat limits
    limits = check_chat_limit(session_id)
    if not limits["can_chat"]:
        return {
            "response": "🔒 Você atingiu o limite de 5 perguntas gratuitas por dia.\n\n💎 **Assine o plano Pro** para perguntas ilimitadas e recursos exclusivos!",
            "limit_reached": True,
            "limits": limits
        }
    
    message = request.message
    
    # Increment chat count
    increment_chat_count(session_id)
    
    # Get complete database snapshot for AI to analyze
    df = get_stock_data()
    
    if df.empty:
        return {"response": "Desculpe, não há dados de ações disponíveis no momento."}
    
    # ========================================
    # SMART PRE-FILTERING BASED ON USER CRITERIA
    # ========================================
    # Detect and apply numeric filters before sending to AI
    
    msg_lower = message.lower()
    filtered_df = df.copy()
    applied_filters = []
    
    # Helper to parse numbers with various formats (1 milhão, 1M, 1.000.000, etc.)
    def parse_number(text):
        text = text.replace('.', '').replace(',', '.').strip()
        multipliers = {'milhao': 1_000_000, 'milhões': 1_000_000, 'milhoes': 1_000_000, 
                       'mi': 1_000_000, 'm': 1_000_000, 'mil': 1_000, 'k': 1_000,
                       'bilhao': 1_000_000_000, 'bilhões': 1_000_000_000, 'bi': 1_000_000_000}
        for word, mult in multipliers.items():
            if word in text.lower():
                num = re.search(r'(\d+(?:[.,]\d+)?)', text)
                if num:
                    return float(num.group(1).replace(',', '.')) * mult
        try:
            return float(text)
        except:
            return None
    
    # Liquidez filter (> X or < X)
    liq_match = re.search(r'liquidez\s*(?:maior|acima|>|superior)\s*(?:que|de|a)?\s*[rR$]*\s*([\d.,]+\s*(?:milhao|milhões|milhoes|mi|m|mil|k|bilhao|bi)?)', msg_lower)
    if liq_match and 'liquidez_2meses' in filtered_df.columns:
        min_liq = parse_number(liq_match.group(1))
        if min_liq:
            filtered_df = filtered_df[filtered_df['liquidez_2meses'] >= min_liq]
            applied_filters.append(f"Liquidez >= R$ {min_liq:,.0f}")
    
    liq_match_lt = re.search(r'liquidez\s*(?:menor|abaixo|<|inferior)\s*(?:que|de|a)?\s*[rR$]*\s*([\d.,]+\s*(?:milhao|milhões|milhoes|mi|m|mil|k|bilhao|bi)?)', msg_lower)
    if liq_match_lt and 'liquidez_2meses' in filtered_df.columns:
        max_liq = parse_number(liq_match_lt.group(1))
        if max_liq:
            filtered_df = filtered_df[filtered_df['liquidez_2meses'] <= max_liq]
            applied_filters.append(f"Liquidez <= R$ {max_liq:,.0f}")
    
    # P/L filter
    pl_match_lt = re.search(r'p/?l\s*(?:menor|abaixo|<)\s*(?:que|de|a)?\s*(\d+(?:[.,]\d+)?)', msg_lower)
    if pl_match_lt and 'p_l' in filtered_df.columns:
        max_pl = float(pl_match_lt.group(1).replace(',', '.'))
        filtered_df = filtered_df[(filtered_df['p_l'] > 0) & (filtered_df['p_l'] <= max_pl)]
        applied_filters.append(f"P/L <= {max_pl}")
    
    pl_match_gt = re.search(r'p/?l\s*(?:maior|acima|>)\s*(?:que|de|a)?\s*(\d+(?:[.,]\d+)?)', msg_lower)
    if pl_match_gt and 'p_l' in filtered_df.columns:
        min_pl = float(pl_match_gt.group(1).replace(',', '.'))
        filtered_df = filtered_df[filtered_df['p_l'] >= min_pl]
        applied_filters.append(f"P/L >= {min_pl}")
    
    # DY filter (> X%)
    dy_match = re.search(r'(?:dy|dividend|dividendo)s?\s*(?:maior|acima|>|superior)\s*(?:que|de|a)?\s*(\d+(?:[.,]\d+)?)\s*%?', msg_lower)
    if dy_match and 'dividend_yield' in filtered_df.columns:
        min_dy = float(dy_match.group(1).replace(',', '.'))
        # Handle both decimal (0.06) and percentage (6) formats
        if filtered_df['dividend_yield'].max() < 1:  # Data is in decimal
            min_dy_decimal = min_dy / 100
            filtered_df = filtered_df[filtered_df['dividend_yield'] >= min_dy_decimal]
        else:
            filtered_df = filtered_df[filtered_df['dividend_yield'] >= min_dy]
        applied_filters.append(f"DY >= {min_dy}%")
    
    # ROE filter (> X%)
    roe_match = re.search(r'roe\s*(?:maior|acima|>|superior)\s*(?:que|de|a)?\s*(\d+(?:[.,]\d+)?)\s*%?', msg_lower)
    if roe_match and 'roe' in filtered_df.columns:
        min_roe = float(roe_match.group(1).replace(',', '.'))
        if filtered_df['roe'].max() < 1:
            min_roe_decimal = min_roe / 100
            filtered_df = filtered_df[filtered_df['roe'] >= min_roe_decimal]
        else:
            filtered_df = filtered_df[filtered_df['roe'] >= min_roe]
        applied_filters.append(f"ROE >= {min_roe}%")
    
    # Build filter context for AI
    filter_context = ""
    if applied_filters:
        filter_context = f"\n⚠️ FILTROS APLICADOS: {', '.join(applied_filters)}\nResultados filtrados: {len(filtered_df)} ações de {len(df)} total.\n"
        # Use filtered data
        df = filtered_df
    
    # ========================================
    # BUILD COMPREHENSIVE AI CONTEXT WITH ALL DATA
    # ========================================
    
    total_stocks = len(df)
    
    # Get all unique sectors from actual database
    sectors = df['setor'].unique().tolist() if 'setor' in df.columns else []
    sectors = [s for s in sectors if s and s != 'N/A']
    
    # Helper function to format percentage
    def fmt_pct(val):
        if pd.isna(val) or val == 0:
            return "0.0%"
        return f"{val * 100:.1f}%" if abs(val) < 1 else f"{val:.1f}%"
    
    # Helper function to format number
    def fmt_num(val):
        if pd.isna(val):
            return "N/A"
        return f"{val:.2f}"
    
    # ========================================
    # TOP 10 AÇÕES BY SUPER SCORE (ALL INDICATORS)
    # ========================================
    top_10_text = ""
    for i, (_, s) in enumerate(df.head(10).iterrows(), 1):
        top_10_text += f"""
{i}. {s['papel']} ({s.get('setor', 'N/A')})
   Score: {fmt_num(s.get('super_score', 0))} | Cotação: R$ {fmt_num(s.get('cotacao', 0))}
   P/L: {fmt_num(s.get('p_l', 0))} | P/VP: {fmt_num(s.get('p_vp', 0))} | DY: {fmt_pct(s.get('dividend_yield', 0))}
   ROE: {fmt_pct(s.get('roe', 0))} | ROIC: {fmt_pct(s.get('roic', 0))} | Liq.2M: R$ {s.get('liquidez_2meses', 0):,.0f}
"""
    
    # ========================================
    # TOP 10 BY LIQUIDEZ (volume negociado)
    # ========================================
    if 'liquidez_2meses' in df.columns:
        top_liq = df.nlargest(10, 'liquidez_2meses')[['papel', 'setor', 'liquidez_2meses', 'super_score']]
        liq_text = "\n".join([f"• {r['papel']} ({r['setor']}): R$ {r['liquidez_2meses']:,.0f}/dia | Score: {r['super_score']:.1f}" 
                             for _, r in top_liq.iterrows()])
    else:
        liq_text = "Dados de liquidez não disponíveis"
    
    # ========================================
    # TOP 10 BY DIVIDEND YIELD
    # ========================================
    top_dy = df[df['dividend_yield'] > 0].nlargest(10, 'dividend_yield')[['papel', 'setor', 'dividend_yield', 'p_l']]
    dy_text = "\n".join([f"• {r['papel']} ({r['setor']}): DY {fmt_pct(r['dividend_yield'])} | P/L: {fmt_num(r['p_l'])}" 
                         for _, r in top_dy.iterrows()])
    
    # ========================================
    # TOP 10 BY ROE (Rentabilidade)
    # ========================================
    top_roe = df[df['roe'] > 0].nlargest(10, 'roe')[['papel', 'setor', 'roe', 'roic']]
    roe_text = "\n".join([f"• {r['papel']} ({r['setor']}): ROE {fmt_pct(r['roe'])} | ROIC: {fmt_pct(r['roic'])}" 
                          for _, r in top_roe.iterrows()])
    
    # ========================================
    # TOP 10 MAIS BARATAS (P/L baixo e positivo)
    # ========================================
    cheap = df[(df['p_l'] > 0) & (df['p_l'] < 100)].nsmallest(10, 'p_l')[['papel', 'setor', 'p_l', 'p_vp']]
    cheap_text = "\n".join([f"• {r['papel']} ({r['setor']}): P/L {fmt_num(r['p_l'])} | P/VP: {fmt_num(r['p_vp'])}" 
                            for _, r in cheap.iterrows()])
    
    # ========================================
    # SETORES COM MELHORES AÇÕES
    # ========================================
    sector_summary = ""
    for sector in sorted(sectors):
        sector_stocks = df[df['setor'] == sector].nlargest(2, 'super_score')[['papel', 'super_score', 'liquidez_2meses']].to_dict(orient='records')
        if sector_stocks:
            top_names = ", ".join([f"{s['papel']}({s['super_score']:.1f})" for s in sector_stocks])
            sector_summary += f"• {sector}: {top_names}\n"
    
    # ========================================
    # DADOS ESPECÍFICOS DE AÇÃO (se mencionada)
    # ========================================
    ticker_pattern = r'\b([A-Z]{4}[0-9]{1,2})\b'
    ticker_match = re.search(ticker_pattern, message.upper())
    specific_stock_info = ""
    
    if ticker_match:
        ticker = ticker_match.group(1)
        stock = df[df['papel'] == ticker]
        if not stock.empty:
            s = stock.iloc[0]
            rank = df[df['papel'] == ticker].index[0] + 1
            specific_stock_info = f"""
═══════════════════════════════════════════════════════
📊 DADOS COMPLETOS DE {ticker} (Ranking #{rank} de {total_stocks})
═══════════════════════════════════════════════════════
Setor: {s.get('setor', 'N/A')} | Subsetor: {s.get('subsetor', 'N/A')}
Cotação: R$ {fmt_num(s.get('cotacao', 0))}

📈 SCORES:
• Super Score: {fmt_num(s.get('super_score', 0))}
• Graham: {fmt_num(s.get('score_graham', 0))}
• Greenblatt: {fmt_num(s.get('score_greenblatt', 0))}
• Bazin: {fmt_num(s.get('score_bazin', 0))}
• Qualidade: {fmt_num(s.get('score_qualidade', 0))}

💰 INDICADORES DE VALOR:
• P/L: {fmt_num(s.get('p_l', 0))}
• P/VP: {fmt_num(s.get('p_vp', 0))}
• P/EBIT: {fmt_num(s.get('p_ebit', 0))}
• EV/EBIT: {fmt_num(s.get('ev_ebit', 0))}
• EV/EBITDA: {fmt_num(s.get('ev_ebitda', 0))}
• PSR: {fmt_num(s.get('psr', 0))}
• P/Ativo: {fmt_num(s.get('p_ativo', 0))}
• P/Cap.Giro: {fmt_num(s.get('p_cap_giro', 0))}
• P/Ativo Circ.Líq.: {fmt_num(s.get('p_ativo_circulante_liq', 0))}

📊 RENTABILIDADE:
• ROE: {fmt_pct(s.get('roe', 0))}
• ROIC: {fmt_pct(s.get('roic', 0))}
• Margem Líquida: {fmt_pct(s.get('margem_liquida', 0))}
• Margem EBIT: {fmt_pct(s.get('margem_ebit', 0))}

📈 DIVIDENDOS E CRESCIMENTO:
• Dividend Yield: {fmt_pct(s.get('dividend_yield', 0))}
• Crescimento Receita 5a: {fmt_pct(s.get('crescimento_receita_5a', 0))}

💧 LIQUIDEZ E PATRIMÔNIO:
• Liquidez Corrente: {fmt_num(s.get('liquidez_corrente', 0))}
• Liquidez Média 2 meses: R$ {s.get('liquidez_2meses', 0):,.0f}/dia
• Patrimônio Líquido: R$ {s.get('patrimonio_liquido', 0):,.0f}
• Dív.Bruta/Patrimônio: {fmt_num(s.get('div_bruta_patrimonio', 0))}
"""
    
    # ========================================
    # SYSTEM PROMPT COMPLETO
    # ========================================
    system_prompt = f"""Você é o Analista de Investimentos IA do TopAções - o mais completo assistente de análise fundamentalista de ações brasileiras.
{filter_context}
═══════════════════════════════════════════════════════
📊 DADOS COMPLETOS DO MERCADO ({len(df)} ações {f'filtradas' if applied_filters else 'analisadas'})
═══════════════════════════════════════════════════════

🏆 TOP 10 AÇÕES POR SUPER SCORE:
{top_10_text}

═══════════════════════════════════════════════════════
💧 TOP 10 POR LIQUIDEZ (Volume diário médio 2 meses):
═══════════════════════════════════════════════════════
{liq_text}

═══════════════════════════════════════════════════════
💰 TOP 10 POR DIVIDEND YIELD:
═══════════════════════════════════════════════════════
{dy_text}

═══════════════════════════════════════════════════════
📈 TOP 10 POR ROE (Rentabilidade):
═══════════════════════════════════════════════════════
{roe_text}

═══════════════════════════════════════════════════════
💸 TOP 10 MAIS BARATAS (menor P/L positivo):
═══════════════════════════════════════════════════════
{cheap_text}

═══════════════════════════════════════════════════════
🏢 TODOS OS SETORES E SUAS MELHORES AÇÕES:
═══════════════════════════════════════════════════════
{sector_summary}
{specific_stock_info}

═══════════════════════════════════════════════════════
📚 GLOSSÁRIO DE INDICADORES (para você entender e explicar):
═══════════════════════════════════════════════════════
INDICADORES DE VALOR:
• P/L (Preço/Lucro) - Quanto menor, mais barata. Ideal < 15.
• P/VP (Preço/Valor Patrimonial) - Quanto menor, mais barata. Ideal < 1.5.
• P/EBIT - Preço sobre lucro operacional.
• EV/EBIT - Enterprise Value sobre lucro operacional. Menor = mais barato.
• EV/EBITDA - Enterprise Value sobre EBITDA.
• PSR (Price/Sales) - Preço sobre Receita.
• P/Ativo - Preço sobre Ativo total.
• P/Cap.Giro - Preço sobre Capital de Giro.

INDICADORES DE RENTABILIDADE:
• ROE (Return on Equity) - Retorno sobre patrimônio. Ideal > 15%.
• ROIC (Return on Invested Capital) - Retorno sobre capital investido. Ideal > 15%.
• Margem Líquida - Lucro líquido / Receita. Quanto maior, melhor.
• Margem EBIT - Lucro operacional / Receita.

INDICADORES DE DIVIDENDOS:
• Dividend Yield (DY) - Dividendos pagos / Preço. Ideal > 6% para Bazin.

INDICADORES DE LIQUIDEZ:
• Liquidez Corrente - Ativo Circulante / Passivo Circulante. Ideal > 1.5.
• Liquidez 2 Meses - Volume médio diário negociado (R$). Quanto maior, mais fácil comprar/vender.

INDICADORES DE ENDIVIDAMENTO:
• Dív.Bruta/Patrimônio - Quanto menor, menos endividada.

INDICADORES DE CRESCIMENTO:
• Crescimento Receita 5a - Crescimento da receita nos últimos 5 anos.

ESTRATÉGIAS:
• Graham: Foco em valor e segurança. Busca P/L baixo (<15), P/VP baixo (<1.5), boa liquidez.
• Greenblatt (Magic Formula): Combina EV/EBIT baixo com ROIC alto.
• Bazin: Foco em dividendos. DY > 6%, baixo endividamento, empresa sólida.
• Qualidade: ROE alto (>15%), ROIC alto, margens saudáveis.

REGRAS:
1. Responda SEMPRE em português brasileiro, de forma clara e amigável.
2. Use APENAS os dados fornecidos acima - não invente dados.
3. Se o usuário perguntar sobre algo que não está nos dados, diga claramente.
4. Formate números adequadamente: R$ 10,50 | 15,5% | Score 12,3
6. Para rankings, use os dados fornecidos nas seções acima."""

    try:
        from groq import Groq
        
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            raise ValueError("GROQ_API_KEY não configurada")
            
        client = Groq(api_key=api_key)
        
        messages = [{"role": "system", "content": system_prompt}]
        
        # Add conversation history
        for msg in request.history[-6:]:
            messages.append({"role": msg.role, "content": msg.content})
        
        messages.append({"role": "user", "content": message})
        
        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=messages,
            temperature=0.7,
            max_tokens=1000
        )
        
        return {"response": completion.choices[0].message.content}
        
    except Exception as e:
        print(f"AI Error: {e}")
        # Simple fallback when Groq fails
        return simple_fallback_response(df)



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



# ============================================
# RELATÓRIO PDF GENERATOR
# ============================================

class PDFReport(FPDF):
    def header(self):
        self.set_font('Arial', 'B', 15)
        self.cell(0, 10, 'TopAções - Relatório Semanal de Mercado', 0, 1, 'C')
        self.ln(5)

    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.cell(0, 10, f'Página {self.page_no()}', 0, 0, 'C')

@app.get("/api/reports/weekly")
async def generate_weekly_report(current_user: dict = Depends(get_current_user)):
    """
    Gera um relatório PDF semanal com os destaques do mercado.
    Apenas para usuários Premium.
    """
    if not current_user.get("is_premium"):
        raise HTTPException(status_code=403, detail="Apenas usuários Premium podem baixar relatórios.")

    try:
        df = get_stock_data()
        if df.empty:
            raise HTTPException(status_code=404, detail="Dados de mercado indisponíveis")

        pdf = PDFReport()
        pdf.add_page()
        pdf.set_font("Arial", size=12)

        # 1. Resumo de Mercado
        pdf.set_font("Arial", "B", 14)
        pdf.cell(200, 10, txt=f"Resumo da Semana - {datetime.now().strftime('%d/%m/%Y')}", ln=True)
        pdf.ln(5)
        
        pdf.set_font("Arial", size=11)
        total_analisadas = len(df)
        media_pl = df['p_l'].mean()
        media_dy = df['dividend_yield'].mean()
        
        resumo = f"""
        Total de ações analisadas: {total_analisadas}
        Média P/L do mercado: {media_pl:.2f}
        Média Dividend Yield: {media_dy:.2f}%
        """
        pdf.multi_cell(0, 7, txt=resumo)
        pdf.ln(5)

        # 2. Top 5 Super Score
        pdf.set_font("Arial", "B", 14)
        pdf.cell(200, 10, txt="🏆 Top 5 Ações (Super Score)", ln=True)
        pdf.ln(5)
        
        pdf.set_font("Arial", size=10)
        top_5 = df.nlargest(5, 'super_score')
        
        # Table Header
        pdf.set_fill_color(200, 220, 255)
        pdf.cell(30, 10, "Ticker", 1, 0, 'C', 1)
        pdf.cell(40, 10, "Setor", 1, 0, 'C', 1)
        pdf.cell(30, 10, "Preço", 1, 0, 'C', 1)
        pdf.cell(30, 10, "Score", 1, 0, 'C', 1)
        pdf.cell(30, 10, "D.Yield", 1, 1, 'C', 1)
        
        # Table Rows
        for _, row in top_5.iterrows():
            pdf.cell(30, 10, str(row['papel']), 1, 0, 'C')
            pdf.cell(40, 10, str(row['setor'])[:15], 1, 0, 'C') # Truncate sector
            pdf.cell(30, 10, f"R$ {row['cotacao']:.2f}", 1, 0, 'C')
            pdf.cell(30, 10, f"{row['super_score']:.1f}", 1, 0, 'C')
            pdf.cell(30, 10, f"{row['dividend_yield']:.1f}%", 1, 1, 'C')
            
        pdf.ln(10)

        # 3. Top Dividendos
        pdf.set_font("Arial", "B", 14)
        pdf.cell(200, 10, txt="💰 Top 5 Dividendos", ln=True)
        pdf.ln(5)
        
        pdf.set_font("Arial", size=10)
        top_dy = df.nlargest(5, 'dividend_yield')
        
        # Table Header
        pdf.set_fill_color(200, 255, 220)
        pdf.cell(30, 10, "Ticker", 1, 0, 'C', 1)
        pdf.cell(40, 10, "Setor", 1, 0, 'C', 1)
        pdf.cell(30, 10, "Preço", 1, 0, 'C', 1)
        pdf.cell(30, 10, "P/L", 1, 0, 'C', 1)
        pdf.cell(30, 10, "D.Yield", 1, 1, 'C', 1)
        
        # Table Rows
        for _, row in top_dy.iterrows():
            pdf.cell(30, 10, str(row['papel']), 1, 0, 'C')
            pdf.cell(40, 10, str(row['setor'])[:15], 1, 0, 'C')
            pdf.cell(30, 10, f"R$ {row['cotacao']:.2f}", 1, 0, 'C')
            pdf.cell(30, 10, f"{row['p_l']:.1f}", 1, 0, 'C')
            pdf.cell(30, 10, f"{row['dividend_yield']:.1f}%", 1, 1, 'C')

        pdf.ln(10)
        pdf.set_font("Arial", "I", 10)
        pdf.multi_cell(0, 7, txt="Nota: Este relatório é gerado automaticamente com base em dados fundamentalistas públicos. Não constitui recomendação de compra ou venda.")

        # Output
        pdf_content = pdf.output(dest='S').encode('latin-1')
        buffer = io.BytesIO(pdf_content)
        buffer.seek(0)
        
        filename = f"topacoes_report_{datetime.now().strftime('%Y%m%d')}.pdf"
        
        return StreamingResponse(
            buffer, 
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
        
    except Exception as e:
        logger.error("pdf_generation_failed", error=str(e))
        raise HTTPException(status_code=500, detail="Erro ao gerar relatório PDF")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)


