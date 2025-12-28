"""
AI Chat Service using Groq API
"""
import requests
from config.settings import GROQ_API_KEY, GROQ_MODEL


SYSTEM_PROMPT = """Você é um consultor de investimento que responde sempre em português do Brasil.
Você entende tudo de investimento, e com os dados fornecidos, você irá atuar em suas respostas.
Sempre traga os links exatos com a mesma informação da onde você encontrou essas informações.
Seja educado e direto. Olhe sempre para sites brasileiros.
Não aceite falar sobre nada que não tenha a ver com investimento ou finanças."""


def chat_with_groq(messages: list) -> str:
    """
    Send chat messages to Groq API and get response.
    
    Args:
        messages: List of message dicts with 'role' and 'content'
        
    Returns:
        AI response text
        
    Raises:
        Exception if API call fails
    """
    url = "https://api.groq.com/openai/v1/chat/completions"
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {GROQ_API_KEY}"
    }
    
    system_message = {"role": "system", "content": SYSTEM_PROMPT}
    
    data = {
        "model": GROQ_MODEL,
        "messages": [system_message] + messages
    }
    
    response = requests.post(url, headers=headers, json=data)
    response.raise_for_status()
    
    return response.json()["choices"][0]["message"]["content"]


def processar_pergunta(texto: str, df=None) -> str:
    """
    Process user question, optionally with stock data context.
    
    Args:
        texto: User question
        df: Optional DataFrame with stock data for context
        
    Returns:
        AI response
    """
    conversa = []
    
    # If DataFrame provided, extract mentioned tickers and add context
    if df is not None and not df.empty:
        papeis = extrair_papeis(texto, df)
        if papeis:
            dados = montar_contexto(papeis, df)
            texto += f" com esses dados: {dados}"
    
    conversa.append({"role": "user", "content": texto})
    resposta = chat_with_groq(conversa)
    
    return resposta


def extrair_papeis(prompt: str, df) -> list:
    """
    Extract stock tickers mentioned in prompt.
    
    Args:
        prompt: User prompt text
        df: DataFrame with stock data
        
    Returns:
        List of mentioned ticker symbols
    """
    if 'papel' not in df.columns:
        return []
    
    return [p for p in df["papel"].str.upper() if p in prompt.upper()]


def montar_contexto(papeis: list, df) -> list:
    """
    Build context data for mentioned stocks.
    
    Args:
        papeis: List of ticker symbols
        df: DataFrame with stock data
        
    Returns:
        List of stock data dictionaries
    """
    return df[df["papel"].isin(papeis)].to_dict(orient="records")
