import json
import requests
from typing import Optional


OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL_NAME = "llama3:8b"

def _ask_ollama(prompt: str, system: str = "") -> str:
    """Envoie un prompt à Ollama et retourne la réponse en texte."""
    payload = {
        "model": MODEL_NAME,
        "prompt": prompt,
        "stream": False,
    }
    if system:
        payload["system"] = system

    try:
        response = requests.post(OLLAMA_URL, json=payload, timeout=120)
        response.raise_for_status()
        return response.json().get("response", "").strip()
    except requests.exceptions.ConnectionError:
        raise ConnectionError(
            "Impossible to join Ollama. "
        )
    except requests.exceptions.Timeout:
        raise TimeoutError("Ollama didn't respond.")