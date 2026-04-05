"""
main.py
=======
FastAPI application entry point.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from db.DB import engine, Base
from api.DataManagerRouter import router as data_router

import models.trainer
import models.learner
import models.room
import models.equipment
import models.course
import models.schedule
import models.constraints

from alembic.config import Config
from alembic import command

from Services.LlmService import _ask_ollama
from api.PlanningRouter import router as planning_router


def init_db():
    Base.metadata.create_all(bind=engine)
    alembic_cfg = Config("alembic.ini")
    command.upgrade(alembic_cfg, "head")
    print("Database initialized and up to date.")


def test_llm_connection() -> bool:
    print("Testing LLM connection (llama3:8b via Ollama)...")
    reply = _ask_ollama(
        prompt="Reply with exactly: LLM_OK",
        system="You are a test bot. Answer only with the token asked.",
    )
    if "LLM_OK" in reply:
        print("LLM operational:", reply)
        return True
    print("Unexpected LLM response:", reply)
    return False


app = FastAPI(
    title="Agentic-AI Planning System",
    description="AI-powered training schedule planning API",
    version="1.0.0",
)

# =============================================================================
#  CORS — Allows the React frontend to send requests to this backend
# =============================================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",   # Vite default (React + Vite)
        "http://localhost:3000",   # Create React App fallback
    ],
    allow_credentials=True,
    allow_methods=["*"],           # GET, POST, PUT, DELETE, OPTIONS
    allow_headers=["*"],           # Content-Type, Authorization, etc.
)

# =============================================================================

app.include_router(planning_router)
app.include_router(data_router)


@app.on_event("startup")
def startup():
    init_db()
    test_llm_connection()


@app.get("/")
def read_root():
    return {"message": "Agentic-AI Planning System is running"}