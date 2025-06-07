import requests
from dotenv import load_dotenv
import os
load_dotenv()


def chat_with_groq(messages: list) -> str:
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {os.getenv('GROQ_API_KEY')}"
    }
    system_prompt = {"role": "system", "content": "Você é um consultor de investimento que responde sempre em português do Brasil, e que entende tudo de investimento, e com os dados fornecidos, você ira atuar em suas respostas. Além disso sempre ira trazer os links exatos com a mesma informação da onde você encontrou essas informações, seja educado e direto. olhe sempre para sites brasileiros. Não aceite falar sobre nada que não tenha haver com investimento ou finanças"}
    data = {
        "model": "compound-beta",
        "messages": [system_prompt] + messages
    }
    response = requests.post(url, headers=headers, json=data)
    response.raise_for_status()
    return response.json()["choices"][0]["message"]["content"]


def mensagem_cli(texto: str) -> str:
    """Envia o texto para o modelo e retorna a resposta."""
    mensagens = [{"role": "user", "content": texto}]
    return chat_with_groq(mensagens)
