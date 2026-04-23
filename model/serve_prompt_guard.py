import os
from functools import lru_cache
from pathlib import Path

import torch
import uvicorn
from fastapi import FastAPI
from huggingface_hub import snapshot_download
from pydantic import BaseModel
from torch.nn.functional import softmax
from transformers import AutoModelForSequenceClassification, AutoTokenizer
from dotenv import load_dotenv
load_dotenv()
from groq import Groq

MODEL_ID = os.getenv("PROMPT_GUARD_MODEL_ID", "meta-llama/Llama-Prompt-Guard-2-86M")
XLMR_MODEL_ID = os.getenv("PROMPT_GUARD_XLMR_MODEL_ID", "alexoladom/prompt_guard_xlmr")
XLMR_MODEL_LOCAL_DIR = Path(
    os.getenv(
        "PROMPT_GUARD_XLMR_LOCAL_DIR",
        str(Path(__file__).resolve().parent / "modelo_final_xlmr_v2"),
    )
)
MODEL_MAX_TOKENS = int(os.getenv("PROMPT_GUARD_MAX_TOKENS", "512"))
MODEL_THRESHOLD = float(os.getenv("PROMPT_GUARD_THRESHOLD", "0.80"))
HOST = os.getenv("PROMPT_GUARD_HOST", "127.0.0.1")
PORT = int(os.getenv("PROMPT_GUARD_PORT", "8001"))
HF_TOKEN = os.getenv("HF_TOKEN")

app = FastAPI(title="Prompt Guard Service")


def _resolve_model_source(model_id: str) -> str:
    candidate = Path(model_id)
    if candidate.exists():
        return str(candidate.resolve())

    relative_candidate = Path(__file__).resolve().parent / model_id
    if relative_candidate.exists():
        return str(relative_candidate.resolve())

    return model_id


def _is_transformers_model_dir(path: Path) -> bool:
    return path.is_dir() and (path / "config.json").exists()


def _resolve_xlmr_model_source() -> str:
    direct_candidate = Path(XLMR_MODEL_ID)
    if _is_transformers_model_dir(direct_candidate):
        return str(direct_candidate.resolve())

    relative_candidate = Path(__file__).resolve().parent / XLMR_MODEL_ID
    if _is_transformers_model_dir(relative_candidate):
        return str(relative_candidate.resolve())

    if _is_transformers_model_dir(XLMR_MODEL_LOCAL_DIR):
        return str(XLMR_MODEL_LOCAL_DIR.resolve())

    print(
        f"Descargando modelo XLM-R desde Hugging Face: {XLMR_MODEL_ID} "
        f"-> {XLMR_MODEL_LOCAL_DIR}"
    )
    downloaded_path = snapshot_download(
        repo_id=XLMR_MODEL_ID,
        local_dir=str(XLMR_MODEL_LOCAL_DIR),
        token=HF_TOKEN,
    )
    return str(Path(downloaded_path).resolve())


@lru_cache(maxsize=2)
def _load_model(model_name: str):
    if model_name == "llama":
        model_id = _resolve_model_source(MODEL_ID)
        tokenizer = AutoTokenizer.from_pretrained(model_id, token=HF_TOKEN)
        model = AutoModelForSequenceClassification.from_pretrained(model_id, token=HF_TOKEN)
    elif model_name == "xlmr":
        model_id = _resolve_xlmr_model_source()
        tokenizer = AutoTokenizer.from_pretrained(model_id, token=HF_TOKEN)
        model = AutoModelForSequenceClassification.from_pretrained(model_id, token=HF_TOKEN)
    else:
        raise ValueError(f"Modelo no soportado: {model_name}")
    model.eval()
    return tokenizer, model


# Preload both models at startup
PRELOADED_MODELS = {}
def preload_models():
    for model_name in ["llama", "xlmr"]:
        try:
            PRELOADED_MODELS[model_name] = _load_model(model_name)
        except Exception as e:
            print(f"Error loading model {model_name}: {e}")

preload_models()


class ClassifyRequest(BaseModel):
    text: str
    model: str = "llama"  # "llama" (default) or "xlmr"


def _severity_from_score(score: float) -> str:
    if score >= 0.95:
        return "CRITICAL"
    if score >= 0.85:
        return "HIGH"
    return "MEDIUM"



def _chunk_text(tokenizer, text: str) -> list[str]:
    encoded = tokenizer(
        text,
        add_special_tokens=False,
        return_attention_mask=False,
        return_token_type_ids=False,
    )
    input_ids = encoded.get("input_ids", [])
    if not input_ids:
        return [text]

    chunks = []
    for start in range(0, len(input_ids), MODEL_MAX_TOKENS):
        chunk_ids = input_ids[start:start + MODEL_MAX_TOKENS]
        chunk_text = tokenizer.decode(chunk_ids, skip_special_tokens=True).strip()
        if chunk_text:
            chunks.append(chunk_text)

    return chunks or [text]


def _classify_text(text: str, model_name: str = "llama") -> dict:
    tokenizer, model = _load_model(model_name)
    chunks = _chunk_text(tokenizer, text)
    best = {
        "label": "BENIGN",
        "score": 0.0,
        "chunk_count": len(chunks),
    }

    with torch.no_grad():
        for chunk in chunks:
            inputs = tokenizer(
                chunk,
                return_tensors="pt",
                truncation=True,
                max_length=MODEL_MAX_TOKENS,
            )
            logits = model(**inputs).logits[0]
            probs = softmax(logits, dim=-1)
            predicted_id = int(torch.argmax(probs).item())
            label = model.config.id2label[predicted_id]
            score = float(probs[predicted_id].item())
            print(f"Chunk: {chunk[:50]}... | Label: {label} | Score: {score:.4f}")
            if model_name == "llama":
                if label == "LABEL_1" and score >= best["score"]:
                    best = {
                        "label": "MALICIOUS",
                        "score": score,
                        "chunk_count": len(chunks),
                    }
                elif best["label"] != "LABEL_1" and score >= best["score"]:
                    best = {
                        "label": "BENIGNO",
                        "score": score,
                        "chunk_count": len(chunks),
                    }
            else:  # xlmr
                if label == "harmful_content" and score >= best["score"]:
                    best = {
                        "label": "CONTENIDO DAÑINO",
                        "score": score,
                        "chunk_count": len(chunks),
                    }
                elif label == "prompt_injection" and score >= best["score"]:
                    best = {
                        "label": "INYECCIÓN DE PROMPT",
                        "score": score,
                        "chunk_count": len(chunks),
                    }
                elif label == "benign" and score >= best["score"]:
                    best = {
                        "label": "BENIGNO",
                        "score": score,
                        "chunk_count": len(chunks),
                    }
    matched = best["label"] != "BENIGNO" and best["score"] >= MODEL_THRESHOLD

    return {
        "matched": matched,
        "label": best["label"],
        "confidence": best["score"],
        "threshold": MODEL_THRESHOLD,
        "chunk_count": best["chunk_count"],
        "rule_name": ("llama_prompt_guard_2_86m_malicious_prompt" if model_name == "llama" else "xlmr_malicious_prompt") if matched else None,
        "category": "PROMPT_ATTACK" if matched else None,
        "severity": _severity_from_score(best["score"]) if matched else None,
        "detection_method": ("prompt_guard_2_86m:text_classification" if model_name == "llama" else "xlmr:text_classification"),
        "model": model_name,
    }


@app.get("/health")
def health():
    _load_model("llama")
    _load_model("xlmr")
    return {"status": "ok", "models": list(PRELOADED_MODELS.keys())}


@app.post("/classify")
def classify(request: ClassifyRequest):
    return _classify_text(request.text, request.model)


if __name__ == "__main__":
    uvicorn.run("model.serve_prompt_guard:app", host=HOST, port=PORT)
