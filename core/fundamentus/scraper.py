"""
Fundamentus Web Scraper
Collects stock data from fundamentus.com.br
"""
import requests
import pandas as pd
from bs4 import BeautifulSoup

from config.settings import FUNDAMENTUS_URL, BLACKLIST_ATIVOS


def carregar_fundamentus() -> pd.DataFrame:
    """
    Fetch stock data from Fundamentus website.
    
    Returns:
        DataFrame with raw stock data
    """
    print("🔄 Carregando dados do Fundamentus...")
    headers = {"User-Agent": "Mozilla/5.0"}
    
    response = requests.get(FUNDAMENTUS_URL, headers=headers)
    response.raise_for_status()
    
    soup = BeautifulSoup(response.content, "html.parser")
    tabela = soup.find("table", {"id": "resultado"})
    
    df = pd.read_html(str(tabela), decimal=",", thousands=".")[0]
    
    return df


def filtrar_blacklist(df: pd.DataFrame) -> pd.DataFrame:
    """
    Remove blacklisted stocks from DataFrame.
    
    Args:
        df: DataFrame with stock data
        
    Returns:
        Filtered DataFrame
    """
    if 'papel' in df.columns:
        df = df[~df['papel'].isin(BLACKLIST_ATIVOS)]
    return df


def buscar_detalhes_ativo(ticker: str) -> dict:
    """
    Fetch detailed info for a specific stock (sector, subsector).
    
    Args:
        ticker: Stock ticker symbol (e.g., 'VALE3')
        
    Returns:
        Dict with 'setor' and 'subsetor'
    """
    from config.settings import FUNDAMENTUS_DETAIL_URL
    
    url = f"{FUNDAMENTUS_DETAIL_URL}{ticker}"
    headers = {"User-Agent": "Mozilla/5.0"}
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, "html.parser")
        
        # Find sector and subsector in the page
        setor = "Não encontrado"
        subsetor = "Não encontrado"
        
        # Look for the table with company info
        tables = soup.find_all("table", {"class": "w728"})
        for table in tables:
            for row in table.find_all("tr"):
                cells = row.find_all("td")
                for i, cell in enumerate(cells):
                    text = cell.get_text(strip=True)
                    if "Setor" in text and i + 1 < len(cells):
                        setor = cells[i + 1].get_text(strip=True)
                    if "Subsetor" in text and i + 1 < len(cells):
                        subsetor = cells[i + 1].get_text(strip=True)
        
        return {"setor": setor, "subsetor": subsetor}
        
    except Exception as e:
        print(f"⚠️ Erro ao buscar detalhes de {ticker}: {e}")
        return {"setor": "Erro", "subsetor": "Erro"}
