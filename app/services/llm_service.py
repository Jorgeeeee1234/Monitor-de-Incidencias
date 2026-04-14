import os
import requests
from requests.exceptions import RequestException
from dotenv import load_dotenv

load_dotenv()


class LLMService:
    def __init__(self):
        self.ollama_url = os.getenv("OLLAMA_URL", "http://localhost:11434/api/generate")
        self.model = os.getenv("OLLAMA_MODEL", "qwen2.5:3b")

    def generate_response(self, prompt: str) -> str:
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False
        }

        try:
            response = requests.post(self.ollama_url, json=payload, timeout=60)
            response.raise_for_status()
            data = response.json()
            return data.get("response", "No se pudo generar respuesta.")
        except RequestException as exc:
            return f"No se pudo conectar con Ollama: {exc}"
