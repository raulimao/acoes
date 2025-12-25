"""
AI Context Service
Provides rich context from database for AI chat responses
"""
import pandas as pd
from typing import Dict, List, Optional, Any
from datetime import datetime

from services.history_service import get_historico
from core.pipeline import carregar_dados_completos
from config.strategies_config import ESTRATEGIAS


def get_stock_details(ticker: str) -> Optional[Dict]:
    """Get complete details for a specific stock."""
    df = carregar_dados_completos()
    stock = df[df['papel'] == ticker.upper()]
    
    if stock.empty:
        return None
    
    row = stock.iloc[0]
    return {
        'papel': row['papel'],
        'setor': row.get('setor', 'N/A'),
        'subsetor': row.get('subsetor', 'N/A'),
        'cotacao': round(float(row.get('cotacao', 0)), 2),
        'p_l': round(float(row.get('p_l', 0)), 2),
        'p_vp': round(float(row.get('p_vp', 0)), 2),
        'dividend_yield': round(float(row.get('dividend_yield', 0)) * 100, 2),
        'roe': round(float(row.get('roe', 0)) * 100, 2),
        'roic': round(float(row.get('roic', 0)) * 100, 2),
        'margem_liquida': round(float(row.get('margem_liquida', 0)) * 100, 2),
        'liquidez_corrente': round(float(row.get('liquidez_corrente', 0)), 2),
        'div_bruta_patrimonio': round(float(row.get('div_bruta_patrimonio', 0)), 2),
        'score_graham': round(float(row.get('score_graham', 0)), 2),
        'score_greenblatt': round(float(row.get('score_greenblatt', 0)), 2),
        'score_bazin': round(float(row.get('score_bazin', 0)), 2),
        'score_qualidade': round(float(row.get('score_qualidade', 0)), 2),
        'super_score': round(float(row.get('super_score', 0)), 2),
    }


def get_stock_evolution(ticker: str, days: int = 180) -> Dict:
    """Get evolution data for a stock over time."""
    df = get_historico(dias=days, papel=ticker.upper())
    
    if df.empty:
        return {'ticker': ticker, 'records': 0, 'evolution': None}
    
    df = df.sort_values('data')
    
    first = df.iloc[0]
    last = df.iloc[-1]
    
    first_score = float(first.get('super_score', 0))
    last_score = float(last.get('super_score', 0))
    change = ((last_score - first_score) / first_score * 100) if first_score > 0 else 0
    
    return {
        'ticker': ticker.upper(),
        'records': len(df),
        'first_date': str(first['data'])[:10],
        'last_date': str(last['data'])[:10],
        'first_score': round(first_score, 2),
        'last_score': round(last_score, 2),
        'change_percent': round(change, 1),
        'trend': 'subindo' if change > 5 else 'caindo' if change < -5 else 'estável'
    }


def compare_stocks(ticker1: str, ticker2: str) -> Dict:
    """Compare two stocks side by side."""
    stock1 = get_stock_details(ticker1)
    stock2 = get_stock_details(ticker2)
    
    if not stock1 or not stock2:
        return {'error': 'Um ou ambos os ativos não foram encontrados'}
    
    indicators = ['p_l', 'p_vp', 'dividend_yield', 'roe', 'roic', 'super_score']
    comparison = {}
    
    for ind in indicators:
        val1 = stock1.get(ind, 0)
        val2 = stock2.get(ind, 0)
        
        # Determine winner (lower is better for P/L, P/VP; higher for others)
        if ind in ['p_l', 'p_vp']:
            winner = ticker1 if val1 < val2 and val1 > 0 else ticker2
        else:
            winner = ticker1 if val1 > val2 else ticker2
        
        comparison[ind] = {
            ticker1: val1,
            ticker2: val2,
            'winner': winner.upper()
        }
    
    return {
        'stock1': stock1,
        'stock2': stock2,
        'comparison': comparison
    }


def get_top_stocks(n: int = 5, strategy: str = None) -> List[Dict]:
    """Get top N stocks, optionally filtered by strategy."""
    df = carregar_dados_completos()
    
    sort_col = 'super_score'
    if strategy:
        strategy_lower = strategy.lower()
        if strategy_lower in ['graham', 'greenblatt', 'bazin', 'qualidade']:
            sort_col = f'score_{strategy_lower}'
    
    df = df.sort_values(sort_col, ascending=False).head(n)
    
    return df[['papel', 'setor', 'super_score', 'score_graham', 'score_greenblatt', 
               'score_bazin', 'score_qualidade', 'cotacao']].fillna(0).to_dict(orient='records')


def get_stocks_by_sector(sector: str) -> List[Dict]:
    """Get stocks filtered by sector."""
    df = carregar_dados_completos()
    
    # Case-insensitive partial match
    mask = df['setor'].str.lower().str.contains(sector.lower(), na=False)
    filtered = df[mask].sort_values('super_score', ascending=False)
    
    if filtered.empty:
        return []
    
    return filtered[['papel', 'setor', 'super_score', 'cotacao', 'p_l', 'dividend_yield']].head(10).fillna(0).to_dict(orient='records')


def get_top_evolutions(days: int = 30, n: int = 5) -> List[Dict]:
    """Get stocks with best score evolution."""
    df = get_historico(dias=days)
    
    if df.empty:
        return []
    
    # Group by ticker and calculate evolution
    evolutions = []
    for ticker in df['papel'].unique():
        ticker_data = df[df['papel'] == ticker].sort_values('data')
        if len(ticker_data) >= 2:
            first = float(ticker_data.iloc[0]['super_score'])
            last = float(ticker_data.iloc[-1]['super_score'])
            if first > 0:
                change = ((last - first) / first) * 100
                evolutions.append({
                    'ticker': ticker,
                    'first_score': round(first, 2),
                    'last_score': round(last, 2),
                    'change': round(change, 1)
                })
    
    # Sort by change and return top N
    evolutions.sort(key=lambda x: x['change'], reverse=True)
    return evolutions[:n]


def search_stocks_by_criteria(
    max_pl: float = None,
    min_dy: float = None,
    min_roe: float = None,
    min_score: float = None,
    sector: str = None
) -> List[Dict]:
    """Search stocks by multiple criteria."""
    df = carregar_dados_completos()
    
    if max_pl is not None:
        df = df[(df['p_l'] > 0) & (df['p_l'] <= max_pl)]
    
    if min_dy is not None:
        df = df[df['dividend_yield'] >= min_dy / 100]  # Convert to decimal
    
    if min_roe is not None:
        df = df[df['roe'] >= min_roe / 100]
    
    if min_score is not None:
        df = df[df['super_score'] >= min_score]
    
    if sector:
        df = df[df['setor'].str.lower().str.contains(sector.lower(), na=False)]
    
    df = df.sort_values('super_score', ascending=False).head(10)
    
    return df[['papel', 'setor', 'super_score', 'p_l', 'p_vp', 'dividend_yield', 'roe']].fillna(0).to_dict(orient='records')


def get_strategy_info(strategy_name: str) -> Optional[Dict]:
    """Get information about an investment strategy."""
    strategies_info = {
        'graham': {
            'name': 'Benjamin Graham',
            'description': 'Foco em valor e segurança. Busca ações subavaliadas com baixo P/L, P/VP e boa liquidez.',
            'key_indicators': ['P/L baixo', 'P/VP baixo', 'Liquidez Corrente alta', 'Baixo endividamento'],
            'ideal_for': 'Investidores conservadores que buscam margem de segurança'
        },
        'greenblatt': {
            'name': 'Joel Greenblatt (Magic Formula)',
            'description': 'Combina empresas baratas (EV/EBIT) com alta rentabilidade (ROIC).',
            'key_indicators': ['EV/EBIT baixo', 'ROIC alto'],
            'ideal_for': 'Investidores que buscam qualidade a preço justo'
        },
        'bazin': {
            'name': 'Décio Bazin',
            'description': 'Foco em dividendos consistentes. Busca empresas que pagam bons dividendos de forma sustentável.',
            'key_indicators': ['Dividend Yield > 6%', 'Baixo endividamento', 'P/L razoável'],
            'ideal_for': 'Investidores focados em renda passiva'
        },
        'qualidade': {
            'name': 'Quality Investing',
            'description': 'Busca empresas de alta qualidade com rentabilidade superior e margens saudáveis.',
            'key_indicators': ['ROE alto', 'ROIC alto', 'Margem líquida alta', 'Baixo endividamento'],
            'ideal_for': 'Investidores de longo prazo focados em qualidade'
        }
    }
    
    key = strategy_name.lower()
    return strategies_info.get(key)


def build_ai_context() -> str:
    """Build comprehensive context for AI assistant."""
    df = carregar_dados_completos()
    
    if df.empty:
        return "Não há dados disponíveis no momento."
    
    # Summary stats
    total = len(df)
    avg_score = df['super_score'].mean()
    top_5 = df.head(5)[['papel', 'super_score', 'setor']].to_dict(orient='records')
    
    # Top per strategy
    top_graham = df.nlargest(3, 'score_graham')[['papel', 'score_graham']].to_dict(orient='records')
    top_greenblatt = df.nlargest(3, 'score_greenblatt')[['papel', 'score_greenblatt']].to_dict(orient='records')
    top_bazin = df.nlargest(3, 'score_bazin')[['papel', 'score_bazin']].to_dict(orient='records')
    
    # Sectors
    sectors = df['setor'].value_counts().head(5).to_dict()
    
    context = f"""
DADOS DO BANCO (Atualizado):
- Total de ações: {total}
- Score médio: {avg_score:.2f}

TOP 5 AÇÕES (Super Score):
{top_5}

TOP POR ESTRATÉGIA:
- Graham: {top_graham}
- Greenblatt: {top_greenblatt}
- Bazin: {top_bazin}

SETORES MAIS REPRESENTADOS:
{sectors}

FUNÇÕES DISPONÍVEIS:
- Consultar ação específica: pergunte sobre qualquer ticker
- Comparar ações: "compare X com Y"
- Evolução histórica: "como evoluiu X"
- Filtrar por setor: "ações do setor X"
- Buscar por critérios: "ações com P/L < 10"
- Explicar estratégias: "explique Graham/Greenblatt/Bazin"
"""
    return context
