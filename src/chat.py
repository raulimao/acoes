import requests
from dotenv import load_dotenv
import os
load_dotenv()

def chat_with_groq(messages: list) -> str:
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {os.getenv("GROQ_API_KEY")}"
    }
    system_prompt = {"role": "system", "content": "Você é um gerente de conta que responde sempre em português do Brasil, e que entende tudo de investimento, e com os dados fornecidos, você ira atuar em suas respostas."}
    data = {
        "model": "compound-beta",
        "messages": [system_prompt] + messages
    }
    response = requests.post(url, headers=headers, json=data)
    response.raise_for_status()
    return response.json()["choices"][0]["message"]["content"]


def mensagem_cli(texto):
    conversa = []

    while True:
        user_input = texto
        if user_input.lower() in ["sair", "exit", "quit"]:
            break

        conversa.append({"role": "user", "content": user_input})
        resposta = chat_with_groq(conversa)
        conversa.append({"role": "assistant", "content": resposta})

        return resposta