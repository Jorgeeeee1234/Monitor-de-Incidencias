import os
from typing import Any

import requests
from requests import RequestException


class AIClassifierUnavailableError(RuntimeError):
    pass


class AIClassifierService:
    DETECTOR_KEY = "AI_CLASSIFIER"

    def __init__(self):
        base_url = os.getenv("PROMPT_GUARD_BASE_URL", "http://127.0.0.1:8001").rstrip("/")
        self.classify_url = os.getenv("PROMPT_GUARD_CLASSIFY_URL", f"{base_url}/classify")
        self.health_url = os.getenv("PROMPT_GUARD_HEALTH_URL", f"{base_url}/health")
        self.timeout = float(os.getenv("PROMPT_GUARD_TIMEOUT", "10"))

    def is_available(self) -> bool:
        try:
            response = requests.get(self.health_url, timeout=min(self.timeout, 2.0))
            response.raise_for_status()
            return True
        except RequestException:
            return False

    def detect(self, text: str, model: str) -> dict[str, Any]:
        payload = {"text": text, "model": model}

        try:
            response = requests.post(self.classify_url, json=payload, timeout=self.timeout)
            response.raise_for_status()
        except RequestException as exc:
            raise AIClassifierUnavailableError(
                "AI Classifier no disponible. Despliega Prompt Guard y verifica PROMPT_GUARD_BASE_URL."
            ) from exc

        data = response.json()
        matched = bool(data.get("matched", False))

        return {
            "matched": matched,
            "rule_name": data.get("rule_name", "llama_prompt_guard_2_86m") if model == "llama" else data.get("rule_name", "xlmr_malicious_prompt"),
            "category": data.get("label") if matched else None,
            "severity": data.get("severity") if matched else None,
            "confidence": float(data.get("confidence", 0.0)) if matched else 0.0,
            "detection_method": data.get("detection_method", "prompt_guard_2") if model == "llama" else data.get("detection_method", "xlmr"),
            "detector_triggered": self.DETECTOR_KEY if matched else None,
            "raw_label": data.get("label"),
        }
