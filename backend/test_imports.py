import sys
from pathlib import Path

# Add backend to path
BACKEND_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BACKEND_DIR))

try:
    print("Testing imports...")
    import fastapi
    print("[OK] fastapi")
    import sqlalchemy
    print("[OK] sqlalchemy")
    import jwt
    print("[OK] jwt (pyjwt)")
    import chromadb
    print("[OK] chromadb")
    import crewai
    print("[OK] crewai")
    
    # Test project local imports
    from database.db import init_db
    print("[OK] Database init import")
    from auth.models import User
    print("[OK] Auth models import")
    from incidents.models import Incident
    print("[OK] Incidents models import")
    from agents.crew import TrafficCommanderCrew
    print("[OK] CrewAI agents import")

    print("Initializing Database...")
    init_db()
    print("[OK] SQLite database initialized successfully!")

    print("Testing RAG initialization...")
    from agents.rag_knowledge import initialize_knowledge_base
    initialize_knowledge_base()
    print("[OK] RAG database initialized successfully!")

    print("\nALL BACKEND CHECKS PASSED SUCCESSFULLY!")
except Exception as e:
    import traceback
    print("\n[ERROR] Test check failed:")
    traceback.print_exc()
    sys.exit(1)
