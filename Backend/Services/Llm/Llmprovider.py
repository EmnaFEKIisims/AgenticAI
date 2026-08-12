"""
Services/LLM/LLMProvider.py
=============================
Abstract interface — all LLM providers must implement generate().
Agents never import Ollama or any Cloud SDK directly.
They only use this interface via LlmService.
"""

from abc import ABC, abstractmethod


class LLMProvider(ABC):

    @abstractmethod
    def generate(self, prompt: str, system: str | None = None) -> str:
        """
        Generate a text response from the LLM.

        Args:
            prompt: user prompt (the task / question)
            system: system instructions (the role / context)

        Returns:
            str — always a plain string, never a dict or object
        """
        pass