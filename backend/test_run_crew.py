import os
import sys
from pathlib import Path

# Add backend directory to path
BACKEND_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BACKEND_DIR))

# Import crew
from agents.crew import TrafficCommanderCrew
from agents.rag_knowledge import initialize_knowledge_base

def main():
    # Load from .env file if it exists
    env_path = Path(__file__).resolve().parent / ".env"
    if env_path.exists():
        print(f"[*] Found .env file at {env_path}, loading variables...")
        for line in env_path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if "=" in line and not line.startswith("#"):
                k, v = line.split("=", 1)
                os.environ[k.strip()] = v.strip().strip('"').strip("'")

    api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
    print("=" * 60)
    print("RUNNING TRAFFIC COMMANDER CREW TEST")
    print("=" * 60)
    print(f"[*] API Key present in environment: {bool(api_key)}")
    if api_key:
        print(f"[*] Key length: {len(api_key)}")
        print(f"[*] Key starts with: {api_key[:8]}...")
        # Sync keys
        os.environ["GEMINI_API_KEY"] = api_key
        os.environ["GOOGLE_API_KEY"] = api_key
    else:
        print("[ERROR] No GOOGLE_API_KEY or GEMINI_API_KEY found in your local environment.")
        print("Please set it in your terminal before running this script.")
        print("Example (PowerShell): $env:GOOGLE_API_KEY=\"AIzaSy...\"")
        print("Example (Cmd): set GOOGLE_API_KEY=AIzaSy...")
        print("=" * 60)
        return

    # Pre-initialize RAG knowledge base
    print("\n[*] Initializing RAG Knowledge base...")
    try:
        initialize_knowledge_base()
        print("[OK] RAG base initialized.")
    except Exception as e:
        print(f"[WARN] RAG initialization failed: {e}")

    # Run Crew
    print("\n[*] Running CrewAI sequential workflow (6 Agents)...")
    try:
        crew = TrafficCommanderCrew()
        results = crew.run(
            incident_description="Waterlogging on MG Road Bangalore near Trinity Circle. 2 lanes submerged. Traffic diverted. Moderate rainfall continuing. Time: 5:00 PM.",
            location="MG Road near Trinity Circle, Bangalore",
            incident_type="Flood"
        )
        print("\n" + "=" * 60)
        print("SUCCESS! CREW RESULTS GENERATED:")
        print("=" * 60)
        for key, value in results.items():
            if key != "crew_output":
                print(f"\n[{key.upper()}] ({value['agent']}):")
                print(f"Tools Used: {value['tools_used']}")
                print("-" * 40)
                print(value['output'])
        print("=" * 60)
    except Exception as e:
        import traceback
        print("\n[CRITICAL ERROR] Crew execution failed:")
        traceback.print_exc()
        print("=" * 60)

if __name__ == "__main__":
    main()
