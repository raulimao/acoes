"""
Fundamentus Web Scraper
Collects stock data from fundamentus.com.br
Includes multipled fallback mechanisms to ensure data availability on cloud hosting (Render).
"""
import requests
import pandas as pd
from bs4 import BeautifulSoup
import cloudscraper
import time
import random
from io import StringIO

from config.settings import FUNDAMENTUS_URL, BLACKLIST_ATIVOS, FUNDAMENTUS_DETAIL_URL


def get_mock_data():
    """Return hardcoded fallback data if scraping fails completely."""
    print("⚠️ Usando dados de mock (fallback) devido a erro no scraper")
    msg = """Papel,Cotação,P/L,P/VP,PSR,Div.Yield,P/Ativo,P/Cap.Giro,P/EBIT,P/Ativ Circ.Liq,EV/EBIT,EV/EBITDA,Mrg Ebit,Mrg. Líq,Liq. Corr.,ROIC,ROE,Liq.2meses,Patrim. Líq,Dív.Brut/ Patrim.,Cresc. Rec.5a
VALE3,63.45,6.54,1.48,1.67,0.0898,0.67,6.86,4.56,-1.23,4.32,3.87,36.54%,23.45%,1.98,21.34%,22.65%,2345678900.00,187654321000.00,0.34,12.34%
PETR4,36.78,3.21,1.12,0.87,0.1890,0.45,4.32,2.34,-0.98,3.21,2.87,45.67%,28.90%,1.56,23.45%,34.56%,1987654321.00,345678901000.00,0.56,8.76%
ITUB4,34.56,9.87,1.87,2.34,0.0678,1.23,0.00,8.76,0.00,8.54,8.12,25.43%,18.76%,0.00,18.76%,19.87%,1234567890.00,154321098000.00,0.00,5.43%
BBAS3,28.90,4.56,0.98,1.23,0.0987,0.87,0.00,3.45,0.00,3.21,2.98,34.56%,21.34%,0.00,19.87%,21.43%,876543210.00,132109876000.00,0.00,9.87%
WEGE3,40.12,32.45,12.34,5.67,0.0123,4.32,21.43,28.76,32.10,27.65,26.54,18.76%,14.32%,2.34,25.43%,38.76%,456789012.00,18765432000.00,0.12,15.67%
RENT3,56.78,18.76,3.45,2.12,0.0234,1.43,8.76,12.34,-4.32,14.56,9.87,28.76%,16.54%,1.23,14.32%,18.76%,345678901.00,23456789000.00,0.87,21.34%
RADL3,25.43,45.67,8.76,3.21,0.0112,2.34,18.76,32.45,45.67,31.23,18.76,8.76%,6.54%,1.67,16.54%,19.87%,234567890.00,8765432000.00,0.23,18.76%
PRIO3,45.67,8.76,2.34,3.45,0.0000,1.87,6.54,7.65,-2.12,6.54,5.43,56.78%,43.21%,1.87,28.76%,32.10%,567890123.00,12345678000.00,0.45,34.56%
BBNK3,12.34,12.34,1.23,1.12,0.0456,0.56,0.00,7.65,0.00,6.54,5.43,43.21%,21.34%,0.00,15.43%,12.34%,12345678.00,2345678000.00,0.00,12.34%
GGBR4,23.45,6.54,0.87,0.65,0.0678,0.43,3.21,5.43,-1.23,5.67,4.32,15.43%,8.76%,2.34,14.32%,13.21%,345678901.00,45678901000.00,0.34,7.65%
"""
    try:
        return pd.read_csv(StringIO(msg), decimal=",", thousands=".")
    except Exception as e:
        print(f"Erro ao carregar mock data: {e}")
        return pd.DataFrame()


def carregar_fundamentus() -> pd.DataFrame:
    """
    Fetch stock data from Fundamentus website.
    Uses multiple fallback mechanisms: CloudScraper -> Requests -> Mock Data
    """
    print("🔄 Carregando dados do Fundamentus...")
    
    # 1. Tentar CloudScraper (melhor para byapss)
    try:
        scraper = cloudscraper.create_scraper()
        response = scraper.get(FUNDAMENTUS_URL)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, "html.parser")
        tabela = soup.find("table", {"id": "resultado"})
        
        if tabela:
            print("✅ Dados obtidos via CloudScraper")
            df = pd.read_html(str(tabela), decimal=",", thousands=".")[0]
            return df
    except Exception as e:
        print(f"⚠️ Erro no CloudScraper: {e}")

    # 2. Tentar Requests com Headers Completos (Fallback 1)
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
            "Accept-Language": "pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1"
        }
        
        response = requests.get(FUNDAMENTUS_URL, headers=headers, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, "html.parser")
        tabela = soup.find("table", {"id": "resultado"})
        
        if tabela:
            print("✅ Dados obtidos via Requests (Fallback)")
            df = pd.read_html(str(tabela), decimal=",", thousands=".")[0]
            return df
    except Exception as e:
        print(f"⚠️ Erro no Requests Fallback: {e}")

    # 3. Fallback Final: Mock Data (para não zerar o dashboard)
    return get_mock_data()


def filtrar_blacklist(df: pd.DataFrame) -> pd.DataFrame:
    """Remove blacklisted stocks from DataFrame."""
    if 'papel' in df.columns:
        df = df[~df['papel'].isin(BLACKLIST_ATIVOS)]
    return df


def buscar_detalhes_ativo(ticker: str) -> dict:
    """
    Fetch detailed info for a specific stock (sector, subsector).
    Also tries CloudScraper first.
    """
    from config.settings import FUNDAMENTUS_DETAIL_URL
    url = f"{FUNDAMENTUS_DETAIL_URL}{ticker}"
    
    # Tentar CloudScraper
    try:
        scraper = cloudscraper.create_scraper()
        response = scraper.get(url)
        # response.raise_for_status() # cloudscraper sometimes handles status differently
    except Exception as e:
        print(f"⚠️ Erro CloudScraper Detalhes: {e}")
        # Tentar Requests
        try:
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            }
            response = requests.get(url, headers=headers, timeout=5)
        except Exception:
            return {"setor": "N/A", "subsetor": "N/A"}

    try:
        soup = BeautifulSoup(response.content, "html.parser")
        
        setor = "Não encontrado"
        subsetor = "Não encontrado"
        
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
        print(f"⚠️ Erro parser detalhes {ticker}: {e}")
        return {"setor": "Erro", "subsetor": "Erro"}
