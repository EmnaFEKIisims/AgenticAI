"""
Services/LLM/CloudLLMProvider.py
===================================
Cloud LLM implementation — OpenAI-compatible API.

Works with:
  - OpenAI (GPT-4o, GPT-3.5)
  - Groq  (llama3-70b, mixtral) ← free tier, fast, recommended for PFE
  - Together AI
  - Any OpenAI-compatible endpoint

Configure via .env:
  CLOUD_LLM_API_KEY=your_key
  CLOUD_LLM_MODEL=llama3-70b-8192       ← Groq example
  CLOUD_LLM_BASE_URL=https://api.groq.com/openai/v1  ← Groq base URL

Groq is free and very fast → ideal when Ollama runs out of RAM.
  pip install groq
  or
  pip install openai  (works for all OpenAI-compatible APIs)
"""

import os
from Services.Llm.Llmprovider import LLMProvider


class CloudLLMProvider(LLMProvider):

    def __init__(self):
        self.api_key  = os.getenv("CLOUD_LLM_API_KEY", "")
        self.model    = os.getenv("CLOUD_LLM_MODEL", "llama3-70b-8192")
        self.base_url = os.getenv("CLOUD_LLM_BASE_URL", None)   # None = default OpenAI

        if not self.api_key:
            raise ValueError(
                "CLOUD_LLM_API_KEY is not set in .env. "
                "Set it to use the cloud LLM provider."
            )

        # Import here to avoid crash if openai is not installed
        try:
            from openai import OpenAI
            self.client = OpenAI(
                api_key  = self.api_key,
                base_url = self.base_url,   # None uses OpenAI default
            )
        except ImportError:
            raise ImportError(
                "openai package is not installed. Run: pip install openai"
            )

        print(f"  [CloudLLMProvider] Model: {self.model}")
        if self.base_url:
            print(f"  [CloudLLMProvider] Base URL: {self.base_url}")

    def generate(self, prompt: str, system: str | None = None) -> str:
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        try:
            response = self.client.chat.completions.create(
                model       = self.model,
                messages    = messages,
                temperature = 0.1,
                max_tokens  = 1024,
            )
            text = response.choices[0].message.content or ""
            print(f"  [Cloud] ✅ {len(text)} chars received.")
            return text.strip()
        except Exception as e:
            print(f"  [Cloud] ❌ {e}")
            return ""