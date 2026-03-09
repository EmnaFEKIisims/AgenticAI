from fastapi import FastAPI
from db.DB import engine
from db.DB  import Base

import models.trainer
import models.learner
import models.room
import models.equipment
import models.course
import models.schedule
from alembic.config import Config
from alembic import command
import alembic.config
import alembic.command
from core.LlmService import _ask_ollama


def init_db():

    #Création des tables s'ils n'existent pas
    Base.metadata.create_all(bind=engine)

    #Modification dans la BD en cas de modification en système
    alembic_cfg = Config("alembic.ini")
    command.upgrade(alembic_cfg, "head")

print("Base de données initialisée et mise à jour (tables créées ou modifiées).")


def test_llm_connection() -> bool:

    print("🔍  Test de connexion au LLM (llama3:8b via Ollama)...")
    reply = _ask_ollama(
        prompt="Reply with exactly: LLM_OK",
        system="You are a test bot. Answer only with the token asked.",
    )
    if "LLM_OK" in reply:
        print("✅  LLM opérationnel ! Réponse :", reply)
        return True
    else:
        print("⚠️  Réponse inattendue :", reply)
        return False


app = FastAPI(
    title="Agentic-AI Planning System",
    on_startup=[init_db ,
                test_llm_connection()]
)


@app.get("/")
def read_root():
    return {"message": "Bienvenue sur l'API du système de planification Agentic-AI"}