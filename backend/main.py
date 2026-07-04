import sys
import os
from pathlib import Path

# Add backend directory to path
BACKEND_DIR = Path(__file__).resolve().parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from database.db import init_db
from auth.router import router as auth_router
from incidents.router import router as incidents_router

app = FastAPI(
    title="AI City Traffic Commander",
    description="AI-powered traffic management system with 6 specialized agents",
    version="1.0.0",
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth_router)
app.include_router(incidents_router)

# Mount frontend static files
FRONTEND_DIR = BACKEND_DIR.parent / "frontend"
if FRONTEND_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(FRONTEND_DIR)), name="static")


@app.on_event("startup")
async def startup_event():
    """Initialize database and RAG knowledge base on startup."""
    init_db()
    # Initialize RAG knowledge base
    try:
        from agents.rag_knowledge import initialize_knowledge_base
        initialize_knowledge_base()
        print("[OK] RAG Knowledge base initialized successfully")
    except Exception as e:
        print(f"[WARN] RAG init skipped: {e}")


@app.get("/api/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "AI City Traffic Commander",
        "agents": 6,
        "rag_enabled": True,
        "version": "1.0.0",
    }


@app.get("/")
async def serve_login():
    """Serve the login page."""
    login_page = FRONTEND_DIR / "index.html"
    if login_page.exists():
        return FileResponse(str(login_page))
    return {"message": "AI City Traffic Commander API is running. Frontend not found."}


@app.get("/dashboard")
async def serve_dashboard():
    """Serve the dashboard page."""
    dashboard_page = FRONTEND_DIR / "dashboard.html"
    if dashboard_page.exists():
        return FileResponse(str(dashboard_page))
    return {"message": "Dashboard page not found."}
