import os
from pathlib import Path
from crewai import Agent
from crewai.tools import tool

BASE_DIR = Path(__file__).resolve().parent.parent
KNOWLEDGE_DIR = BASE_DIR / "knowledge_base"

# Global ChromaDB collection reference
_collection = None


def initialize_knowledge_base():
    """Initialize the ChromaDB vector store with traffic knowledge documents."""
    global _collection
    try:
        import chromadb
        from chromadb.config import Settings

        # Create persistent ChromaDB client
        chroma_dir = BASE_DIR / "chroma_db"
        chroma_dir.mkdir(parents=True, exist_ok=True)
        
        client = chromadb.PersistentClient(path=str(chroma_dir))

        # Delete existing collection to refresh
        try:
            client.delete_collection("traffic_knowledge")
        except Exception:
            pass

        _collection = client.get_or_create_collection(
            name="traffic_knowledge",
            metadata={"description": "Traffic rules, emergency SOPs, signal guidelines, and diversion policies"}
        )

        # Load all knowledge documents
        documents = []
        metadatas = []
        ids = []
        doc_id = 0

        if KNOWLEDGE_DIR.exists():
            for md_file in KNOWLEDGE_DIR.glob("*.md"):
                content = md_file.read_text(encoding="utf-8")
                # Split into chunks of ~500 characters for better retrieval
                chunks = _chunk_text(content, chunk_size=500, overlap=50)
                for i, chunk in enumerate(chunks):
                    documents.append(chunk)
                    metadatas.append({
                        "source": md_file.name,
                        "chunk_index": i,
                        "category": md_file.stem.replace("_", " ").title(),
                    })
                    ids.append(f"doc_{doc_id}")
                    doc_id += 1

        if documents:
            _collection.add(
                documents=documents,
                metadatas=metadatas,
                ids=ids,
            )
            print(f"[RAG] Loaded {len(documents)} chunks from {len(list(KNOWLEDGE_DIR.glob('*.md')))} knowledge documents")
        else:
            print("[RAG] No knowledge documents found")

    except Exception as e:
        print(f"[RAG] Error initializing knowledge base: {e}")
        _collection = None


def _chunk_text(text: str, chunk_size: int = 500, overlap: int = 50) -> list[str]:
    """Split text into overlapping chunks."""
    chunks = []
    lines = text.split("\n")
    current_chunk = ""
    
    for line in lines:
        if len(current_chunk) + len(line) > chunk_size and current_chunk:
            chunks.append(current_chunk.strip())
            # Keep overlap
            words = current_chunk.split()
            overlap_words = words[-overlap // 5:] if len(words) > overlap // 5 else words
            current_chunk = " ".join(overlap_words) + "\n" + line
        else:
            current_chunk += "\n" + line if current_chunk else line
    
    if current_chunk.strip():
        chunks.append(current_chunk.strip())
    
    return chunks if chunks else [text]


@tool("RAG Knowledge Search Tool")
def rag_search_tool(query: str) -> str:
    """Searches the traffic knowledge base using semantic search (RAG) powered by ChromaDB vector database. Retrieves relevant traffic rules, emergency SOPs, road diversion policies, and signal guidelines based on the query. Returns the most relevant knowledge chunks with their source documents."""
    import json
    global _collection
    
    if _collection is None:
        initialize_knowledge_base()
    
    if _collection is None:
        return json.dumps({"error": "Knowledge base not initialized", "results": []})
    
    try:
        results = _collection.query(
            query_texts=[query],
            n_results=5,
        )
        
        knowledge_results = []
        if results and results["documents"]:
            for i, doc in enumerate(results["documents"][0]):
                metadata = results["metadatas"][0][i] if results["metadatas"] else {}
                distance = results["distances"][0][i] if results.get("distances") else None
                knowledge_results.append({
                    "content": doc,
                    "source": metadata.get("source", "unknown"),
                    "category": metadata.get("category", "unknown"),
                    "relevance_score": round(1 - (distance or 0), 3) if distance is not None else None,
                })
        
        return json.dumps({
            "query": query,
            "results_count": len(knowledge_results),
            "knowledge": knowledge_results,
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
        max_iter=10,
        max_execution_time=120,
    )
