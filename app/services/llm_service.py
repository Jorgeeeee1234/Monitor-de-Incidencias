import os
import time
import requests
from requests.exceptions import RequestException
from dotenv import load_dotenv

load_dotenv()

_MAX_RETRIES = 3
_RETRY_BASE_DELAY = 2  # seconds; multiplied by attempt number


class LLMService:
    def __init__(self):
        self.ollama_url = os.getenv("OLLAMA_URL", "http://localhost:11434/api/generate")
        self.model = os.getenv("OLLAMA_MODEL", "qwen2.5:3b")

    def generate_response(self, prompt: str) -> str:
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
        }

        last_exc = None
        for attempt in range(_MAX_RETRIES):
            try:
                response = requests.post(self.ollama_url, json=payload, timeout=60)
                response.raise_for_status()
                data = response.json()
                return data.get("response", "No se pudo generar respuesta.")
            except RequestException as exc:
                last_exc = exc
                if attempt < _MAX_RETRIES - 1:
                    time.sleep(_RETRY_BASE_DELAY * (attempt + 1))

        return f"No se pudo conectar con Ollama tras {_MAX_RETRIES} intentos: {last_exc}"
