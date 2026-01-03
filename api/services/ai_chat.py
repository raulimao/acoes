"""
AI Chat Service - Modularized Chat Logic
Handles AI-powered chat with stock market data context
"""
import os
import re
import pandas as pd
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel
from dotenv import load_dotenv

# Ensure environment variables are loaded
load_dotenv()

from config.settings import GROQ_API_KEY, GROQ_MODEL



# ============================================
# MODELS
# ============================================

class ChatMessage(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    message: str
    history: Optional[List[ChatMessage]] = []


# ============================================
# CHAT LIMITS
# ============================================

# Storage (in production, use Redis or database)
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


# ============================================
# HELPER FUNCTIONS
# ============================================

def parse_number(text: str) -> Optional[float]:
    """Parse numbers with various formats (1 milhão, 1M, 1.000.000, etc.)"""
    text = text.replace('.', '').replace(',', '.').strip()
    multipliers = {
        'milhao': 1_000_000, 'milhões': 1_000_000, 'milhoes': 1_000_000, 
        'mi': 1_000_000, 'm': 1_000_000, 'mil': 1_000, 'k': 1_000,
        'bilhao': 1_000_000_000, 'bilhões': 1_000_000_000, 'bi': 1_000_000_000
    }
    for word, mult in multipliers.items():
        if word in text.lower():
            num = re.search(r'(\d+(?:[.,]\d+)?)', text)
            if num:
                return float(num.group(1).replace(',', '.')) * mult
    try:
        return float(text)
    except:
        return None


def fmt_pct(val) -> str:
    """Format value as percentage."""
    if pd.isna(val) or val == 0:
        return "0.0%"
    return f"{val * 100:.1f}%" if abs(val) < 1 else f"{val:.1f}%"


def fmt_num(val) -> str:
    """Format number."""
    if pd.isna(val):
        return "N/A"
    return f"{val:.2f}"


# ============================================
# SMART FILTERING
# ============================================

def apply_smart_filters(df: pd.DataFrame, message: str) -> tuple:
    """
    Apply smart filters based on user message.
    Returns (filtered_df, applied_filters list)
    """
    msg_lower = message.lower()
    filtered_df = df.copy()
    applied_filters = []
    
    # Liquidez filter (> X)
    liq_match = re.search(r'liquidez\s*(?:maior|acima|>|superior)\s*(?:que|de|a)?\s*[rR$]*\s*([\d.,]+\s*(?:milhao|milhões|milhoes|mi|m|mil|k|bilhao|bi)?)', msg_lower)
    if liq_match and 'liquidez_2meses' in filtered_df.columns:
        min_liq = parse_number(liq_match.group(1))
        if min_liq:
            filtered_df = filtered_df[filtered_df['liquidez_2meses'] >= min_liq]
            applied_filters.append(f"Liquidez >= R$ {min_liq:,.0f}")
    
    # Liquidez filter (< X)
    liq_match_lt = re.search(r'liquidez\s*(?:menor|abaixo|<|inferior)\s*(?:que|de|a)?\s*[rR$]*\s*([\d.,]+\s*(?:milhao|milhões|milhoes|mi|m|mil|k|bilhao|bi)?)', msg_lower)
    if liq_match_lt and 'liquidez_2meses' in filtered_df.columns:
        max_liq = parse_number(liq_match_lt.group(1))
        if max_liq:
            filtered_df = filtered_df[filtered_df['liquidez_2meses'] <= max_liq]
            applied_filters.append(f"Liquidez <= R$ {max_liq:,.0f}")
    
    # P/L filter (< X)
    pl_match_lt = re.search(r'p/?l\s*(?:menor|abaixo|<)\s*(?:que|de|a)?\s*(\d+(?:[.,]\d+)?)', msg_lower)
    if pl_match_lt and 'p_l' in filtered_df.columns:
        max_pl = float(pl_match_lt.group(1).replace(',', '.'))
        filtered_df = filtered_df[(filtered_df['p_l'] > 0) & (filtered_df['p_l'] <= max_pl)]
        applied_filters.append(f"P/L <= {max_pl}")
    
    # P/L filter (> X)
    pl_match_gt = re.search(r'p/?l\s*(?:maior|acima|>)\s*(?:que|de|a)?\s*(\d+(?:[.,]\d+)?)', msg_lower)
    if pl_match_gt and 'p_l' in filtered_df.columns:
        min_pl = float(pl_match_gt.group(1).replace(',', '.'))
        filtered_df = filtered_df[filtered_df['p_l'] >= min_pl]
        applied_filters.append(f"P/L >= {min_pl}")
    
    # DY filter (> X%)
    dy_match = re.search(r'(?:dy|dividend|dividendo)s?\s*(?:maior|acima|>|superior)\s*(?:que|de|a)?\s*(\d+(?:[.,]\d+)?)\s*%?', msg_lower)
    if dy_match and 'dividend_yield' in filtered_df.columns:
        min_dy = float(dy_match.group(1).replace(',', '.'))
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
    
    return filtered_df, applied_filters


# ============================================
# CONTEXT BUILDING
# ============================================

def build_market_context(df: pd.DataFrame, message: str, applied_filters: list) -> str:
    """Build comprehensive AI context with all market data."""
    
    total_stocks = len(df)
    sectors = df['setor'].unique().tolist() if 'setor' in df.columns else []
    sectors = [s for s in sectors if s and s != 'N/A']
    
    # Filter context
    filter_context = ""
    if applied_filters:
        filter_context = f"\n⚠️ FILTROS APLICADOS: {', '.join(applied_filters)}\nResultados filtrados: {len(df)} ações.\n"
    
    # TOP 10 by Super Score
    top_10_text = ""
    for i, (_, s) in enumerate(df.head(10).iterrows(), 1):
        top_10_text += f"""
{i}. {s['papel']} ({s.get('setor', 'N/A')})
   Score: {fmt_num(s.get('super_score', 0))} | Cotação: R$ {fmt_num(s.get('cotacao', 0))}
   P/L: {fmt_num(s.get('p_l', 0))} | P/VP: {fmt_num(s.get('p_vp', 0))} | DY: {fmt_pct(s.get('dividend_yield', 0))}
   ROE: {fmt_pct(s.get('roe', 0))} | ROIC: {fmt_pct(s.get('roic', 0))} | Liq.2M: R$ {s.get('liquidez_2meses', 0):,.0f}
"""
    
    # TOP 10 by Liquidez
    if 'liquidez_2meses' in df.columns:
        top_liq = df.nlargest(10, 'liquidez_2meses')[['papel', 'setor', 'liquidez_2meses', 'super_score']]
        liq_text = "\n".join([f"• {r['papel']} ({r['setor']}): R$ {r['liquidez_2meses']:,.0f}/dia | Score: {r['super_score']:.1f}" 
                             for _, r in top_liq.iterrows()])
    else:
        liq_text = "Dados de liquidez não disponíveis"
    
    # TOP 10 by Dividend Yield
    top_dy = df[df['dividend_yield'] > 0].nlargest(10, 'dividend_yield')[['papel', 'setor', 'dividend_yield', 'p_l']]
    dy_text = "\n".join([f"• {r['papel']} ({r['setor']}): DY {fmt_pct(r['dividend_yield'])} | P/L: {fmt_num(r['p_l'])}" 
                         for _, r in top_dy.iterrows()])
    
    # TOP 10 by ROE
    top_roe = df[df['roe'] > 0].nlargest(10, 'roe')[['papel', 'setor', 'roe', 'roic']]
    roe_text = "\n".join([f"• {r['papel']} ({r['setor']}): ROE {fmt_pct(r['roe'])} | ROIC: {fmt_pct(r['roic'])}" 
                          for _, r in top_roe.iterrows()])
    
    # TOP 10 cheaper (low P/L)
    cheap = df[(df['p_l'] > 0) & (df['p_l'] < 100)].nsmallest(10, 'p_l')[['papel', 'setor', 'p_l', 'p_vp']]
    cheap_text = "\n".join([f"• {r['papel']} ({r['setor']}): P/L {fmt_num(r['p_l'])} | P/VP: {fmt_num(r['p_vp'])}" 
                            for _, r in cheap.iterrows()])
    
    # Sectors summary
    sector_summary = ""
    for sector in sorted(sectors):
        sector_stocks = df[df['setor'] == sector].nlargest(2, 'super_score')[['papel', 'super_score']].to_dict(orient='records')
        if sector_stocks:
            top_names = ", ".join([f"{s['papel']}({s['super_score']:.1f})" for s in sector_stocks])
            sector_summary += f"• {sector}: {top_names}\n"
    
    # Specific stock info (if mentioned)
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
• P/L: {fmt_num(s.get('p_l', 0))} | P/VP: {fmt_num(s.get('p_vp', 0))}
• EV/EBIT: {fmt_num(s.get('ev_ebit', 0))} | EV/EBITDA: {fmt_num(s.get('ev_ebitda', 0))}

📊 RENTABILIDADE:
• ROE: {fmt_pct(s.get('roe', 0))} | ROIC: {fmt_pct(s.get('roic', 0))}
• Margem Líquida: {fmt_pct(s.get('margem_liquida', 0))}

📈 DIVIDENDOS:
• Dividend Yield: {fmt_pct(s.get('dividend_yield', 0))}

💧 LIQUIDEZ:
• Liquidez Média 2 meses: R$ {s.get('liquidez_2meses', 0):,.0f}/dia
• Dív.Bruta/Patrimônio: {fmt_num(s.get('div_bruta_patrimonio', 0))}
"""
    
    # Build full system prompt
    system_prompt = f"""Você é o Analista de Investimentos IA do NorteAcoes - o mais completo assistente de análise fundamentalista de ações brasileiras.
{filter_context}
═══════════════════════════════════════════════════════
📊 DADOS COMPLETOS DO MERCADO ({len(df)} ações {'filtradas' if applied_filters else 'analisadas'})
═══════════════════════════════════════════════════════

🏆 TOP 10 AÇÕES POR SUPER SCORE:
{top_10_text}

═══════════════════════════════════════════════════════
💧 TOP 10 POR LIQUIDEZ:
═══════════════════════════════════════════════════════
{liq_text}

═══════════════════════════════════════════════════════
💰 TOP 10 POR DIVIDEND YIELD:
═══════════════════════════════════════════════════════
{dy_text}

═══════════════════════════════════════════════════════
📈 TOP 10 POR ROE:
═══════════════════════════════════════════════════════
{roe_text}

═══════════════════════════════════════════════════════
💸 TOP 10 MAIS BARATAS (menor P/L):
═══════════════════════════════════════════════════════
{cheap_text}

═══════════════════════════════════════════════════════
🏢 SETORES E SUAS MELHORES AÇÕES:
═══════════════════════════════════════════════════════
{sector_summary}
{specific_stock_info}

═══════════════════════════════════════════════════════
📚 GLOSSÁRIO DE INDICADORES:
═══════════════════════════════════════════════════════
• P/L (Preço/Lucro) - Quanto menor, mais barata. Ideal < 15.
• P/VP (Preço/Valor Patrimonial) - Ideal < 1.5.
• ROE (Return on Equity) - Ideal > 15%.
• ROIC (Return on Invested Capital) - Ideal > 15%.
• Dividend Yield (DY) - Ideal > 6% para Bazin.
• Liquidez 2 Meses - Volume médio diário negociado (R$).

ESTRATÉGIAS:
• Graham: P/L baixo (<15), P/VP baixo (<1.5), boa liquidez.
• Greenblatt: EV/EBIT baixo + ROIC alto.
• Bazin: DY > 6%, baixo endividamento.
• Qualidade: ROE alto (>15%), ROIC alto.

═══════════════════════════════════════════════════════
⚠️ REGRAS DE FORMATAÇÃO (MUITO IMPORTANTE):
═══════════════════════════════════════════════════════

1. ESTRUTURA OBRIGATÓRIA:
   - Use títulos com emojis: ## 🏆 Título
   - Separe seções com linhas em branco
   - Use listas numeradas para rankings
   - Use tabelas quando comparar múltiplos ativos

2. FORMATAÇÃO DE AÇÕES:
   Para cada ação, use este formato em LINHAS SEPARADAS:
   
   **1. TICKER (Setor)**
   - 📊 Score: X.X
   - 💰 DY: X.X% | P/L: X.X | P/VP: X.X
   - 📈 ROE: X.X% | ROIC: X.X%
   - 💧 Liquidez: R$ X.XXX/dia
   
   (linha em branco entre cada ação)

3. NUNCA faça:
   - Tudo em uma linha só
   - Textos corridos sem quebras
   - Listas sem espaçamento

4. SEMPRE faça:
   - Quebra de linha após cada indicador
   - Emojis para visual appeal
   - Resumo final com recomendação
   - Responda em português brasileiro"""
    
    return system_prompt


# ============================================
# MAIN CHAT FUNCTION
# ============================================

def simple_fallback_response(df: pd.DataFrame) -> dict:
    """Simple fallback when Groq API fails."""
    if df.empty:
        return {"response": "Desculpe, não há dados disponíveis no momento."}
    
    top_5 = df.head(5)[['papel', 'setor', 'super_score']].to_dict(orient='records')
    response = "🏆 **Top 5 ações por Super Score:**\n\n"
    for i, s in enumerate(top_5, 1):
        response += f"{i}. **{s['papel']}** ({s['setor']}) - Score: {s['super_score']:.1f}\n"
    response += "\n💡 Para análises mais detalhadas, verifique se a API Groq está configurada."
    return {"response": response}


def process_chat(request: ChatRequest, df: pd.DataFrame, session_id: str = "anonymous") -> dict:
    """
    Process chat request with AI.
    
    Args:
        request: ChatRequest with message and history
        df: DataFrame with stock data
        session_id: User session ID for rate limiting
        
    Returns:
        dict with response and optional metadata
    """
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
    
    if df.empty:
        return {"response": "Desculpe, não há dados de ações disponíveis no momento."}
    
    # Apply smart filters
    filtered_df, applied_filters = apply_smart_filters(df, message)
    
    # Use filtered data
    if applied_filters:
        df = filtered_df
    
    # Build context
    system_prompt = build_market_context(df, message, applied_filters)
    
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
        return simple_fallback_response(df)
