import os
import json
import httpx
from pathlib import Path
from crewai import Agent
from crewai.tools import tool

BASE_DIR = Path(__file__).resolve().parent.parent
KNOWLEDGE_DIR = BASE_DIR / "knowledge_base"
EMBEDDINGS_CACHE_FILE = BASE_DIR / "knowledge_embeddings.json"

# In-memory storage for loaded chunks
_knowledge_chunks = []


def get_embedding(text: str, api_key: str) -> list[float]:
    """Get text embedding from Gemini API using httpx."""
    # Using text-embedding-004 model
    url = f"https://generativelanguage.googleapis.com/v1beta/models/text-embedding-004:embedContent?key={api_key}"
    payload = {
        "model": "models/text-embedding-004",
        "content": {
            "parts": [{"text": text}]
        }
    }
    with httpx.Client(timeout=15.0) as client:
        response = client.post(url, json=payload)
        if response.status_code == 200:
            return response.json()["embedding"]["values"]
        else:
            raise Exception(f"Gemini Embedding API error: {response.text}")


def initialize_knowledge_base():
    """Load or generate embeddings for traffic knowledge base using Gemini API."""
    global _knowledge_chunks
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        print("[RAG] WARNING: GOOGLE_API_KEY not set. Cannot initialize knowledge base embeddings.")
        return

    # Check if cache file exists
    if EMBEDDINGS_CACHE_FILE.exists():
        try:
            with open(EMBEDDINGS_CACHE_FILE, "r", encoding="utf-8") as f:
                _knowledge_chunks = json.load(f)
            print(f"[RAG] Loaded {len(_knowledge_chunks)} chunks from local cache file '{EMBEDDINGS_CACHE_FILE.name}'.")
            return
        except Exception as e:
            print(f"[RAG] Failed to load cache file: {e}. Re-generating...")

    # Otherwise, chunk markdown documents and get embeddings
    _knowledge_chunks = []
    if not KNOWLEDGE_DIR.exists():
        print(f"[RAG] Knowledge directory {KNOWLEDGE_DIR} not found.")
        return

    documents_to_process = list(KNOWLEDGE_DIR.glob("*.md"))
    print(f"[RAG] Generating embeddings for {len(documents_to_process)} files using Gemini API...")

    for md_file in documents_to_process:
        try:
            content = md_file.read_text(encoding="utf-8")
            chunks = _chunk_text(content, chunk_size=500, overlap=50)
            for i, chunk in enumerate(chunks):
                # Get embedding via API
                import time
                time.sleep(2.0)  # Wait 2 seconds to respect the 15 RPM free tier rate limit
                embedding = get_embedding(chunk, api_key)
                _knowledge_chunks.append({
                    "content": chunk,
                    "source": md_file.name,
                    "category": md_file.stem.replace("_", " ").title(),
                    "embedding": embedding
                })
                print(f"  [+] Embedded {md_file.name} chunk {i+1}/{len(chunks)}")
        except Exception as e:
            print(f"[RAG] Error processing file {md_file.name}: {e}")

    # Save to cache file
    if _knowledge_chunks:
        try:
            with open(EMBEDDINGS_CACHE_FILE, "w", encoding="utf-8") as f:
                json.dump(_knowledge_chunks, f, indent=2)
            print(f"[RAG] Generated and cached {len(_knowledge_chunks)} chunks successfully.")
        except Exception as e:
            print(f"[RAG] Failed to write cache file: {e}")


def _chunk_text(text: str, chunk_size: int = 500, overlap: int = 50) -> list[str]:
    """Split text into overlapping chunks."""
    chunks = []
    lines = text.split("\n")
    current_chunk = ""
    
    for line in lines:
        if len(current_chunk) + len(line) > chunk_size and current_chunk:
            chunks.append(current_chunk.strip())
            words = current_chunk.split()
            overlap_words = words[-overlap // 5:] if len(words) > overlap // 5 else words
            current_chunk = " ".join(overlap_words) + "\n" + line
        else:
            current_chunk += "\n" + line if current_chunk else line
    
    if current_chunk.strip():
        chunks.append(current_chunk.strip())
    
    return chunks if chunks else [text]


def cosine_similarity(v1, v2):
    """Calculate the cosine similarity between two vectors."""
    dot = sum(x * y for x, y in zip(v1, v2))
    mag1 = sum(x * x for x in v1) ** 0.5
    mag2 = sum(x * x for x in v2) ** 0.5
    if not mag1 or not mag2:
        return 0.0
    return dot / (mag1 * mag2)


@tool("RAG Knowledge Search Tool")
def rag_search_tool(query: str) -> str:
    """Searches the traffic knowledge base using semantic search (RAG) powered by Gemini embeddings. Retrieves relevant traffic rules, emergency SOPs, road diversion policies, and signal guidelines based on the query. Returns the most relevant knowledge chunks with their source documents."""
    global _knowledge_chunks
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        return json.dumps({"error": "GOOGLE_API_KEY not set. Cannot perform RAG search.", "results": []})

    if not _knowledge_chunks:
        initialize_knowledge_base()

    if not _knowledge_chunks:
        return json.dumps({"error": "Knowledge base not initialized or empty", "results": []})

    try:
        # Get query embedding
        query_emb = get_embedding(query, api_key)
        
        # Calculate similarity with all chunks
        scored_chunks = []
        for chunk in _knowledge_chunks:
            sim = cosine_similarity(query_emb, chunk["embedding"])
            scored_chunks.append({
                "content": chunk["content"],
                "source": chunk["source"],
                "category": chunk["category"],
                "relevance_score": round(sim, 3)
            })

        # Sort by relevance and take top 5
        scored_chunks.sort(key=lambda x: x["relevance_score"], reverse=True)
        top_chunks = scored_chunks[:5]

        return json.dumps({
            "query": query,
            "results_count": len(top_chunks),
            "knowledge": top_chunks
        }, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e), "results": []})


def create_rag_knowledge_agent(llm) -> Agent:
    """Creates the Traffic Knowledge RAG Agent - Agent 3."""
    return Agent(
        role="Traffic Knowledge Expert",
        goal="Search the traffic knowledge base using RAG to retrieve relevant traffic rules, emergency response SOPs, road diversion policies, and signal guidelines that support decision-making for the current incident.",
        backstory=(
            "You are a traffic law and policy expert with encyclopedic knowledge of traffic regulations. "
            "You have access to a comprehensive knowledge base containing traffic rules, emergency standard operating procedures, "
            "signal timing guidelines, and road diversion policies. You always search the knowledge base thoroughly "
            "to find the most relevant regulations and guidelines for each incident. Your retrieved knowledge "
            "directly informs emergency routing and signal optimization decisions."
        ),
        tools=[rag_search_tool],
        llm=llm,
        verbose=True,
        max_iter=3,
        max_execution_time=120,
    )
