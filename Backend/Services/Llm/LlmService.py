"""
Services/LLM/LlmService.py
============================
Ollama en priorité → Groq en secours automatique.

Flux :
  1. Essaie Ollama (3 tentatives)
  2. Si Ollama échoue ou timeout → bascule sur Groq automatiquement
  3. Si Groq aussi échoue → retourne ""

Vos agents ne changent rien — ils appellent juste generate() ou _ask_ollama().

.env requis :
  OLLAMA_MODEL=llama3.2:3b
  CLOUD_LLM_API_KEY=gsk_xxxxx
  CLOUD_LLM_MODEL=llama3-70b-8192
  CLOUD_LLM_BASE_URL=https://api.groq.com/openai/v1
"""

import os

from Services.Llm.OllamaProvider  import OllamaProvider
from Services.Llm.CloudlImprovider import CloudLLMProvider


# =============================================================================
#  PROVIDERS — créés une seule fois
# =============================================================================

def _get_ollama() -> OllamaProvider:
    model = os.getenv("OLLAMA_MODEL", "llama3.2:3b")
    return OllamaProvider(model=model)


def _get_cloud() -> CloudLLMProvider | None:
    """Retourne None si la clé API n'est pas configurée."""
    key = os.getenv("CLOUD_LLM_API_KEY", "")
    if not key:
        return None
    try:
        return CloudLLMProvider()
    except Exception as e:
        print(f"  [LlmService] ⚠️  Cloud non disponible : {e}")
        return None


# =============================================================================
#  FONCTION PRINCIPALE — fallback automatique
# =============================================================================

def generate(prompt: str, system: str | None = None) -> str:
    """
    Ollama en priorité, Groq en secours automatique.

    1. Essaie Ollama → si réponse valide → retourne la réponse
    2. Si Ollama échoue → essaie Groq → si réponse valide → retourne la réponse
    3. Si les deux échouent → retourne ""
    """

    # ── ÉTAPE 1 : Ollama ──────────────────────────────────────────────────────
    print("  [LlmService] 🔵 Tentative Ollama...")
    try:
        ollama   = _get_ollama()
        response = ollama.generate(prompt=prompt, system=system)
        if response and response.strip():
            print("  [LlmService] ✅ Ollama a répondu.")
            return response
        else:
            print("  [LlmService] ⚠️  Ollama : réponse vide.")
    except Exception as e:
        print(f"  [LlmService] ⚠️  Ollama a échoué : {e}")

    # ── ÉTAPE 2 : Groq (fallback) ─────────────────────────────────────────────
    print("  [LlmService] 🟡 Bascule sur Groq (Cloud)...")
    cloud = _get_cloud()

    if cloud is None:
        print("  [LlmService] ❌ Groq non configuré (CLOUD_LLM_API_KEY manquante).")
        print("               Ajoutez votre clé Groq dans .env")
        return ""

    try:
        response = cloud.generate(prompt=prompt, system=system)
        if response and response.strip():
            print("  [LlmService] ✅ Groq a répondu (fallback).")
            return response
        else:
            print("  [LlmService] ❌ Groq : réponse vide.")
    except Exception as e:
        print(f"  [LlmService] ❌ Groq a échoué : {e}")

    return ""


# =============================================================================
#  ALIAS — vos agents existants ne changent rien
# =============================================================================

def _ask_ollama(prompt: str, system: str = "") -> str:
    """Alias pour la compatibilité avec votre code existant."""
    return generate(prompt=prompt, system=system or None)


# =============================================================================
#  TEST DE CONNEXION — appelé dans main.py
# =============================================================================

def test_connection() -> bool:
    print("\n  [LlmService] Test de connexion...")
    response = generate(
        prompt = "Reply with exactly: LLM_OK",
        system = "Reply only with the token asked."
    )
    ok = "LLM_OK" in response
    print(f"  [LlmService] {'✅ OK' if ok else '❌ FAILED'}")
    return ok