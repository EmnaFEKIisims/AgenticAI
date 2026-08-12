import os
from dotenv import load_dotenv
load_dotenv()  # ← DOIT être avant tous les autres imports

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from contextlib import asynccontextmanager

# Database & Models
from db.DB import engine, Base, SessionLocal
import models.trainer
import models.learner
import models.room
import models.equipment
import models.course
import models.schedule
import models.constraints

# Alembic
from alembic.config import Config
from alembic import command

# LLM Service — import correct (LLM en majuscules)
from Services.Llm.LlmService import test_connection

# Routers
from api.DataManagerRouter  import router as data_router
from api.PlanningRouter     import router as planning_router
from api.ConstraintRouter   import router as constraint_router
from api.PedagogicalRouter  import router as pedagogical_router


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# =============================================================================
#  TEST LLM — teste Ollama ET Cloud au démarrage
# =============================================================================

def test_llm_connection() -> bool:
    """
    Teste les 2 providers au démarrage.
    Ollama → prioritaire.
    Groq   → fallback automatique si Ollama échoue.
    """
    print("\n" + "="*50)
    print("  LLM CONNECTION TEST")
    print("="*50)

    # ── Test Ollama ────────────────────────────────────────────────────────────
    print("\n  [1/2] Testing Ollama...")
    ollama_ok = False
    try:
        import requests
        model = os.getenv("OLLAMA_MODEL", "llama3.2:3b")
        resp  = requests.post(
            "http://localhost:11434/api/generate",
            json={"model": model, "prompt": "Reply: LLM_OK",
                  "stream": False, "keep_alive": 0,
                  "options": {"num_ctx": 512}},
            timeout=60
        )
        if resp.status_code == 200 and "LLM_OK" in resp.json().get("response", ""):
            print(f"  ✅ Ollama ({model}) — OK")
            ollama_ok = True
        else:
            print(f"  ⚠️  Ollama — réponse inattendue")
    except Exception as e:
        print(f"  ⚠️  Ollama — non disponible : {type(e).__name__}")

    # ── Test Groq Cloud ────────────────────────────────────────────────────────
    print("\n  [2/2] Testing Groq Cloud...")
    cloud_ok = False
    api_key  = os.getenv("CLOUD_LLM_API_KEY", "")
    if not api_key:
        print("  ⚠️  Groq — CLOUD_LLM_API_KEY non configurée dans .env")
    else:
        try:
            from openai import OpenAI
            client = OpenAI(
                api_key  = api_key,
                base_url = os.getenv("CLOUD_LLM_BASE_URL", "https://api.groq.com/openai/v1"),
            )
            resp = client.chat.completions.create(
                model    = os.getenv("CLOUD_LLM_MODEL", "llama3-70b-8192"),
                messages = [{"role": "user", "content": "Reply with exactly: LLM_OK"}],
                max_tokens=10, temperature=0.1
            )
            text = resp.choices[0].message.content or ""
            if "LLM_OK" in text:
                print(f"  ✅ Groq ({os.getenv('CLOUD_LLM_MODEL')}) — OK")
                cloud_ok = True
            else:
                print(f"  ⚠️  Groq — réponse inattendue : {text}")
        except Exception as e:
            print(f"  ⚠️  Groq — erreur : {e}")

    # ── Résumé ─────────────────────────────────────────────────────────────────
    print("\n" + "="*50)
    if ollama_ok and cloud_ok:
        print("  ✅ Ollama + Groq opérationnels (fallback actif)")
    elif ollama_ok:
        print("  ✅ Ollama opérationnel | ⚠️  Groq non disponible")
    elif cloud_ok:
        print("  ⚠️  Ollama non disponible | ✅ Groq opérationnel (fallback actif)")
    else:
        print("  ❌ Aucun LLM disponible — le projet ne fonctionnera pas")
    print("="*50 + "\n")

    return ollama_ok or cloud_ok   # True si au moins un fonctionne


# =============================================================================
#  LIFESPAN
# =============================================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("🚀 Starting Agentic AI Planning System...")

    Base.metadata.create_all(bind=engine)
    alembic_cfg = Config("alembic.ini")
    command.upgrade(alembic_cfg, "head")
    print("✅ Database initialized.")

    test_llm_connection()

    yield
    print("🛑 Shutting down...")


# =============================================================================
#  APP
# =============================================================================

app = FastAPI(
    title       = "Agentic-AI Planning System",
    description = "AI-powered training schedule planning API",
    version     = "1.0.0",
    lifespan    = lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins     = ["http://localhost:5173", "http://localhost:3000"],
    allow_credentials = True,
    allow_methods     = ["*"],
    allow_headers     = ["*"],
)

app.include_router(planning_router)
app.include_router(data_router)
app.include_router(constraint_router)
app.include_router(pedagogical_router)


@app.get("/")
def read_root():
    return {"message": "Agentic-AI Planning System is running", "status": "ok"}