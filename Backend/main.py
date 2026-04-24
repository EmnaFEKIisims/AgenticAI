import os
from fastapi import FastAPI, Depends
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

# LLM Service
from Services.LlmService import _ask_ollama

# Routers
from api.DataManagerRouter import router as data_router
from api.PlanningRouter import router as planning_router

# Orchestrator
from orchestration.Orchestrator import Orchestrator


# Dependency for DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# =============================================================================
# LIFESPAN (moderne, remplace @app.on_event("startup"))
# =============================================================================
@asynccontextmanager
async def lifespan(app: FastAPI):
    print("🚀 Starting Agentic AI Planning System...")

    # Initialize Database + Migrations
    Base.metadata.create_all(bind=engine)
    alembic_cfg = Config("alembic.ini")
    command.upgrade(alembic_cfg, "head")
    print("Database initialized and up to date.")

    # Test LLM connection
    if test_llm_connection():
        print("LLM (Ollama + llama3:8b) is ready.")
    else:
        print("Warning: LLM connection failed! Make sure Ollama is running.")

    yield  # Server runs here

    print("Shutting down Agentic AI Planning System...")


# =============================================================================
# FastAPI App
# =============================================================================
app = FastAPI(
    title="Agentic-AI Planning System",
    description="AI-powered training schedule planning API",
    version="1.0.0",
    lifespan=lifespan,
)


# =============================================================================
# CORS
# =============================================================================
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",   # Vite (React + TypeScript)
        "http://localhost:3000",   # Fallback
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# =============================================================================
# Include Routers
# =============================================================================
app.include_router(planning_router)
app.include_router(data_router)




# =============================================================================
# Root endpoint
# =============================================================================
@app.get("/")
def read_root():
    return {
        "message": "Agentic-AI Planning System is running",
        "status": "ok"
    }


# =============================================================================
# LLM Test Function (kept from your original)
# =============================================================================
def test_llm_connection() -> bool:
    print("Testing LLM connection (llama3:8b via Ollama)...")
    try:
        reply = _ask_ollama(
            prompt="Reply with exactly: LLM_OK",
            system="You are a test bot. Answer only with the token asked."
        )
        if "LLM_OK" in reply:
            print(f"LLM operational: {reply.strip()}")
            return True
        else:
            print(f"Unexpected LLM response: {reply}")
            return False
    except Exception as e:
        print(f"LLM connection error: {e}")
        return False