# 🚦 AI City Traffic Commander

AI City Traffic Commander is a full-stack, AI-powered traffic management system built using the **CrewAI agentic framework**. It orchestrates six specialized AI agents to analyze incidents, predict congestion, query emergency guidelines, plan emergency vehicle routing, optimize traffic signals, and generate public warnings. The application features dual JWT & API Key authentication and a stunning dashboard interface.

---

## 📄 Project Summary

### 1. What problem are you solving, and who will use it?
Urban traffic congestion costs billions annually and delays emergency response vehicles, costing lives. **AI City Traffic Commander** provides real-time, automated coordination between traffic monitoring, congestion analysis, emergency dispatch, and public notification systems. 

**Target Users**: City Traffic Operations Centers, emergency services (Ambulance, Police, Fire), urban planners, and municipal authorities.

### 2. How many agents are there, and what do they do?
There are **six** specialized AI agents collaborating in a sequential pipeline. Every agent is equipped with custom tools to perform real operations rather than just text generation:

| Agent | Role | Custom Tools Used | Purpose |
|-------|------|-------------------|---------|
| **1. Traffic Monitor** | Traffic Monitoring Officer | `Weather Lookup Tool`, `Geocode Location Tool` | Validates incident location, looks up live weather, and extracts structured data. |
| **2. Congestion Analyst** | Traffic Data Analyst | `Traffic Density Calculator Tool`, `Historical Incidents Database Tool` | Models congestion severity (1-10), delay time, and checks database for historical patterns. |
| **3. Traffic Knowledge RAG** | Traffic Knowledge Expert | `RAG Knowledge Search Tool` (ChromaDB) | Performs semantic searches over standard operating procedures (SOPs) and rules. |
| **4. Emergency Route Planner** | Emergency Navigation Specialist | `Emergency Route Calculator Tool`, `Geocode Location Tool` | Recommends primary and alternate routing for Ambulance, Police, and Fire trucks. |
| **5. Traffic Signal Optimizer** | Smart Signal Control Engineer | `Signal Timing Optimizer Tool`, `Signal Config File Writer Tool` | Adjusts green/yellow/red phases and writes configuration files for physical signals. |
| **6. Public Notifier** | Public Information Officer | `Public Alert Generator Tool`, `Alert File Writer Tool` | Generates formatted alerts (SMS, Email, Social) and writes alert files for distribution. |

### 3. How is RAG (Retrieval-Augmented Generation) used?
A specialized **RAG agent** queries an embedded **ChromaDB vector store** populated with traffic and emergency response documents located in `backend/knowledge_base/`:
- `traffic_rules.md`: Speeds, priority rules, and lane discipline.
- `emergency_sops.md`: Accident and Hazmat response guidelines.
- `signal_guidelines.md`: Phase timing and coordination parameters.
- `diversion_policies.md`: Detour setup and road closure policies.

These documents are chunked and loaded into ChromaDB at startup. The RAG agent uses the query parameter to retrieve the top 5 most relevant guidelines dynamically, ensuring the route planning and signal optimization comply with local laws and standard protocols.

### 4. Why did you use multiple agents instead of a single ChatGPT prompt?
A single LLM prompt cannot handle the complexity of this workflow:
- **Separation of Concerns**: Each agent focuses on a single domain (e.g., routing or signal timing) to prevent context dilution.
- **Stateful Tool Integration**: Agents make independent decisions on when and how to call tools (e.g. Geocoding coordinates before calculating routing ETAs).
- **Sequential Context Dependency**: The output of one agent serves as the validated input for the next (e.g. the Route Planner relies on the Congestion Analyst's quantitative delay predictions).
- **Execution Constraints**: CrewAI manages individual agent retries, token usage monitoring, and execution time caps.

---

## 🛠️ Tech Stack
- **Backend**: FastAPI, SQLAlchemy (SQLite), PyJWT, Uvicorn
- **Agent Framework**: CrewAI v1.x, litellm
- **Vector DB / Embeddings**: ChromaDB, Google Gemini (via litellm)
- **Frontend**: HTML5, Vanilla JS, CSS3 (Glassmorphism design system)
- **Deployment**: Docker, Render

---

## 🚀 Getting Started

### Prerequisites
- Python 3.11+
- Google Gemini API Key (obtain from [Google AI Studio](https://aistudio.google.com/))

### Installation
1. Clone the repository:
   ```bash
   git clone <your-repo-link>
   cd ai-traffic-commander
   ```

2. Set up virtual environment and install dependencies:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r backend/requirements.txt
   ```

3. Set up environment variables:
   ```bash
   # On Windows (Command Prompt):
   set GOOGLE_API_KEY=your_gemini_api_key_here
   
   # On Windows (PowerShell):
   $env:GOOGLE_API_KEY="your_gemini_api_key_here"
   
   # On Linux/macOS:
   export GOOGLE_API_KEY="your_gemini_api_key_here"
   ```

4. Run the development server:
   ```bash
   cd backend
   python main.py
   ```
5. Open your browser and navigate to `http://localhost:10000` or `http://localhost:8000`.

---

## 🔑 Authentication Architecture
The system implements secure dual authentication:
1. **JWT Bearer Token**: Session token returned on `/api/auth/login` to secure the frontend dashboard.
2. **API Keys**: Programmatic UUID tokens generated in the API Keys panel, allowing IoT traffic sensors to submit incident reports directly to `/api/incidents/analyze` via the `X-API-Key` header.
