import requests
import pandas as pd
import numpy as np
from bs4 import BeautifulSoup
import os

# -------------------------------
# Funções principais
# -------------------------------

def carregar_fundamentus():
    print("🔄 Carregando dados do Fundamentus...")
    url = "https://www.fundamentus.com.br/resultado.php"
    headers = {"User-Agent": "Mozilla/5.0"}
    r = requests.get(url, headers=headers)
    r.raise_for_status()
    soup = BeautifulSoup(r.content, "html.parser")
    tabela = soup.find("table", {"id": "resultado"})
    df = pd.read_html(str(tabela), decimal=",", thousands=".")[0]
    return df

def renomear_colunas(df):
    mapping = {
        "Papel":"papel","Cotação":"cotacao","P/L":"p_l","P/VP":"p_vp","PSR":"psr",
        "Div.Yield":"dividend_yield","P/Ativo":"p_ativo","P/Cap.Giro":"p_cap_giro",
        "P/EBIT":"p_ebit","P/Ativ Circ.Liq":"p_ativo_circulante_liq",
        "EV/EBIT":"ev_ebit","EV/EBITDA":"ev_ebitda","Mrg Ebit":"margem_ebit",
        "Mrg. Líq.":"margem_liquida","Liq. Corr.":"liquidez_corrente",
        "ROIC":"roic","ROE":"roe","Liq.2meses":"liquidez_2meses",
        "Patrim. Líq":"patrimonio_liquido","Dív.Brut/ Patrim.":"div_bruta_patrimonio",
        "Cresc. Rec.5a":"crescimento_receita_5a"
    }
    df = df.rename(columns=mapping)
    df.columns = df.columns.str.lower().str.replace(r"[^\w]+", "_", regex=True)
    return df

def limpar_valores(df, skip_cols=["papel"]):
    print("🧹 Limpando e convertendo valores...")
    for col in df.columns:
        if col in skip_cols:
            continue
        if df[col].dtype == object:
            df[col] = df[col].astype(str).str.strip()
            # valores "-" indicam dados ausentes e nao devem remover o sinal de numeros negativos
            df[col] = df[col].replace("-", np.nan)
            df[col] = (
                df[col]
                    .str.replace(".", "", regex=False)
                    .str.replace(",", ".", regex=False)
                    .str.replace("%", "", regex=False)
            )
            df[col] = pd.to_numeric(df[col], errors="coerce")
    return df

def corrigir_p_ativo_e_psr(df):
    for col in ["p_ativo", "psr"]:
        if col in df.columns:
            df[col] = df[col].apply(lambda x: x / 1000 if pd.notna(x) and x > 100 else x)
    return df

def corrigir_cotacoes(df):
    def ajustar(x):
        if pd.isna(x):
            return x
        if x > 1000 or (x > 100 and x % 1 == 0):
            return x / 100
        return x
    df["cotacao"] = df["cotacao"].apply(ajustar)
    return df

# -------------------------------
# Score
# -------------------------------

criterios = {
    "p_l":       ("<", 15),
    "p_vp":      ("<=", 1.5),
    "psr":       ("<=", 1.5),
    "dividend_yield": (">", 4),
    "p_ativo":   ("<=", 1.5),
    "p_cap_giro":(">=", 1),
    "p_ebit":    ("<", 12),
    "p_ativo_circulante_liq":("<", 1.5),
    "ev_ebit":   ("<", 10),
    "ev_ebitda": ("<", 8),
    "margem_ebit":(">=", 10),
    "margem_liquida":(">=", 5),
    "liquidez_corrente":(">=", 1.5),
    "roic":      (">", 10),
    "roe":       (">", 15),
    "div_bruta_patrimonio":("<", 0.5),
}

def calcular_score(row):
    total = len(criterios)
    pontos = 0
    for indicador, (op, ideal) in criterios.items():
        valor = row.get(indicador)
        if pd.isna(valor): continue
        if op in ("<", "<="):
            if valor > 0:
                pontos += min(1, ideal / valor)
        else:
            pontos += min(1, valor / ideal)
    return round((pontos / total) * 100, 2)

# -------------------------------
# Execução
# -------------------------------

def resultado():
    try:
        df = carregar_fundamentus()
        df = renomear_colunas(df)
        df = limpar_valores(df)
        df = corrigir_p_ativo_e_psr(df)
        df = corrigir_cotacoes(df)
        df["score"] = df.apply(calcular_score, axis=1)
        df_ranked = df.sort_values("score", ascending=False).reset_index(drop=True)
    
        return df_ranked
    except Exception as e:
        print(f"❌ Erro ao processar os dados: {e}")
        return pd.DataFrame()


#if __name__ == "__main__":
#    main()
