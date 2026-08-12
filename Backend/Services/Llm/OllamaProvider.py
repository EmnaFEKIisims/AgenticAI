"""
Services/LLM/OllamaProvider.py
================================
Ollama implementation of LLMProvider.

Includes retry logic + RAM optimizations from LlmService fix:
  - keep_alive = 0     → unloads model after each call (saves RAM)
  - num_ctx    = 2048  → smaller context window (less RAM per call)
  - 3 retries with exponential backoff (2s → 4s → 8s)
  - Timeout per attempt (90s)

Model RAM comparison:
  llama3:8b              → ~4.7 GB  (too heavy for most dev machines)
  llama3:8b-instruct-q4_0 → ~2.4 GB  (quantized — good compromise)
  llama3.2:3b            → ~1.5 GB  (recommended)
  llama3.2:1b            → ~0.7 GB  (minimum viable)
"""

import time
import requests

from Services.Llm.Llmprovider import LLMProvider


OLLAMA_URL  = "http://localhost:11434/api/generate"
MAX_RETRIES = 3
RETRY_DELAY = 2     # seconds (doubles each retry)
TIMEOUT_S   = 90


class OllamaProvider(LLMProvider):

    def __init__(self, model: str = "llama3.2:3b"):
        self.model = model
        print(f"  [OllamaProvider] Model: {self.model}")

    def generate(self, prompt: str, system: str | None = None) -> str:
        payload = {
            "model":      self.model,
            "prompt":     prompt,
            "system":     system or "",
            "stream":     False,
            "keep_alive": 0,       # ← unload after call → saves RAM
            "options": {
                "num_ctx":     2048,   # ← smaller context → less RAM
                "temperature": 0.1,
                "top_p":       0.9,
            }
        }

        delay = RETRY_DELAY
        for attempt in range(1, MAX_RETRIES + 1):
            try:
                print(f"  [Ollama] Attempt {attempt}/{MAX_RETRIES}...")
                resp = requests.post(OLLAMA_URL, json=payload, timeout=TIMEOUT_S)
                resp.raise_for_status()
                text = resp.json().get("response", "").strip()
                if not text:
                    raise ValueError("Empty response from Ollama.")
                print(f"  [Ollama] ✅ {len(text)} chars received.")
                return text

            except requests.exceptions.ConnectionError:
                print(f"  [Ollama] ❌ Cannot connect. Is 'ollama serve' running?")
            except requests.exceptions.Timeout:
                print(f"  [Ollama] ⚠️  Timeout after {TIMEOUT_S}s.")
            except Exception as e:
                print(f"  [Ollama] ⚠️  {e}")

            if attempt < MAX_RETRIES:
                print(f"  [Ollama] Retrying in {delay}s...")
                time.sleep(delay)
                delay *= 2

        print(f"  [Ollama] ❌ All retries failed. Returning empty string.")
        return ""