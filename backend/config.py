import os
from pathlib import Path

# Base paths
BASE_DIR = Path(__file__).resolve().parent
KNOWLEDGE_BASE_DIR = BASE_DIR / "knowledge_base"
ALERTS_OUTPUT_DIR = BASE_DIR / "outputs" / "alerts"
SIGNAL_CONFIG_DIR = BASE_DIR / "outputs" / "signal_configs"
DB_PATH = BASE_DIR / "traffic_commander.db"

# Create output directories
ALERTS_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
SIGNAL_CONFIG_DIR.mkdir(parents=True, exist_ok=True)

# Environment variables
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "")
if GOOGLE_API_KEY:
    os.environ["GEMINI_API_KEY"] = GOOGLE_API_KEY
    os.environ["GOOGLE_API_KEY"] = GOOGLE_API_KEY

JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "traffic-commander-secret-key-change-in-production")
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_HOURS = 24

# LLM Config
LLM_MODEL = "gemini/gemini-2.0-flash"

# Database URL
DATABASE_URL = f"sqlite:///{DB_PATH}"
