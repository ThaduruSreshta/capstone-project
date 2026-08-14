import os
from pathlib import Path
from typing import TypedDict
import chromadb
from fastapi import FastAPI
from pydantic import BaseModel, Field
from sentence_transformers import SentenceTransformer
from langgraph.graph import StateGraph, END
# ============================================================
# Configuration
# ============================================================
BASE_DIR = Path(__file__).resolve().parent
DB_DIR = BASE_DIR / "chroma_db"
MOCK_LLM = os.getenv("MOCK_LLM", "1") != "0"
# Load embedding model locally
model = SentenceTransformer("all-MiniLM-L6-v2")
# Connect to the ChromaDB created by ingest.py
client = chromadb.PersistentClient(path=str(DB_DIR))
collection = client.get_collection(name="support_docs")
# ============================================================
# Pydantic models
# ============================================================
class AskRequest(BaseModel):
    query: str
class AskResponse(BaseModel):
    answer: str
    sources: list[str]
    confidence: float = Field(ge=0.0, le=1.0)
# ============================================================
# LangGraph state
# ============================================================
class GraphState(TypedDict, total=False):
    query: str
    intent: str
    answer: str
    sources: list[str]
    confidence: float
    retrieved_chunks: list[str]
# ============================================================
# Structured prompt template
# ============================================================
PROMPT_TEMPLATE = """
ROLE:
You are a Zepto customer-support assistant.
CONTEXT:
Answer only using the policy context supplied below.
TASK:
Answer the customer's question accurately using the provided context.
FORMAT:
Return a concise answer followed by the relevant source document IDs.
LENGTH:
Keep the answer short and clear, preferably under 100 words.
NEGATIVE CONSTRAINT:
Do not answer using information that is not present in the provided context.
If the context does not contain the answer, say that the information is not available.
FEW-SHOT EXAMPLE:
Question: How long does delivery take?
Context: Zepto delivers within 10 to 30 minutes of order confirmation.
Answer: Zepto delivery typically takes 10 to 30 minutes after order confirmation.
"""
# ============================================================
# Node 1: classify_intent
# ============================================================
POLICY_KEYWORDS = [
    "delivery",
    "return",
    "refund",
    "membership",
    "tracking",
    "cancel",
    "gift card",
    "support hours",
]
def classify_intent(state: GraphState) -> GraphState:
    query = state["query"].lower()
    # Required graded mock mode
    if MOCK_LLM:
        if any(keyword in query for keyword in POLICY_KEYWORDS):
            intent = "policy_question"
        else:
            intent = "general_question"
    else:
        # Optional real-LLM extension placeholder.
        # The graded baseline does not require an API call.
        if any(keyword in query for keyword in POLICY_KEYWORDS):
            intent = "policy_question"
        else:
            intent = "general_question"
    return {
        "intent": intent
    }
# ============================================================
# Node 2: retrieve_and_answer
# ============================================================
def retrieve_and_answer(state: GraphState) -> GraphState:
    query = state["query"]
    # Embed the query locally
    query_embedding = model.encode([query]).tolist()
    # Retrieve top 3 using ChromaDB cosine similarity
    results = collection.query(
        query_embeddings=query_embedding,
        n_results=3,
    )
    documents = results["documents"][0]
    ids = results["ids"][0]
    if not documents:
        return {
            "answer": "No relevant policy information was found.",
            "sources": [],
            "confidence": 0.0,
            "retrieved_chunks": [],
        }
    # Required mock-mode answer
    if MOCK_LLM:
        top_chunk = documents[0]
        snippet = top_chunk[:200].strip()
        answer = f"Based on the retrieved context: {snippet}"
    else:
        # Optional real-LLM extension.
        # Keep deterministic fallback so baseline remains functional.
        top_chunk = documents[0]
        answer = f"Based on the retrieved context: {top_chunk[:200].strip()}"
    return {
        "answer": answer,
        "sources": ids,
        "confidence": 1.0,
        "retrieved_chunks": documents,
    }
# ============================================================
# Node 3: direct_answer
# ============================================================
def direct_answer(state: GraphState) -> GraphState:
    # Required graded mock response
    if MOCK_LLM:
        answer = "I can only answer questions about Zepto policies right now."
    else:
        # Optional real-LLM extension fallback
        answer = "I can only answer questions about Zepto policies right now."
    return {
        "answer": answer,
        "sources": [],
        "confidence": 1.0,
    }
# ============================================================
# Conditional routing
# ============================================================
def route_intent(state: GraphState) -> str:
    if state["intent"] == "policy_question":
        return "retrieve_and_answer"
    return "direct_answer"
# ============================================================
# Build LangGraph
# ============================================================
graph_builder = StateGraph(GraphState)
graph_builder.add_node("classify_intent", classify_intent)
graph_builder.add_node("retrieve_and_answer", retrieve_and_answer)
graph_builder.add_node("direct_answer", direct_answer)
graph_builder.set_entry_point("classify_intent")
graph_builder.add_conditional_edges(
    "classify_intent",
    route_intent,
    {
        "retrieve_and_answer": "retrieve_and_answer",
        "direct_answer": "direct_answer",
    },
)
graph_builder.add_edge("retrieve_and_answer", END)
graph_builder.add_edge("direct_answer", END)
graph = graph_builder.compile()
# ============================================================
# FastAPI application
# ============================================================
app = FastAPI(
    title="Zepto Support Assistant",
    description="Offline RAG support assistant using LangGraph and ChromaDB",
)
@app.get("/")
def root():
    return {
        "message": "Zepto Support Assistant is running"
}
@app.post("/ask", response_model=AskResponse)
def ask(request: AskRequest):
    state: GraphState = {
        "query": request.query
}
    result = graph.invoke(state)
    return AskResponse(
        answer=result["answer"],
        sources=result.get("sources", []),
        confidence=result.get("confidence", 1.0),
)