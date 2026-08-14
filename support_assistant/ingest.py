from pathlib import Path

import chromadb
from sentence_transformers import SentenceTransformer


# Paths
BASE_DIR = Path(__file__).resolve().parent
DOCS_DIR = BASE_DIR / "docs"
DB_DIR = BASE_DIR / "chroma_db"

print("Loading embedding model...")
model = SentenceTransformer("all-MiniLM-L6-v2")

print("Creating ChromaDB...")
client = chromadb.PersistentClient(path=str(DB_DIR))

collection = client.get_or_create_collection(
    name="support_docs"
)

# Read documents
documents = []
ids = []
metadatas = []

for file_path in sorted(DOCS_DIR.glob("*.txt")):
    text = file_path.read_text(encoding="utf-8").strip()

    if text:
        documents.append(text)
        ids.append(file_path.stem)
        metadatas.append({"source": file_path.name})

print(f"Found {len(documents)} documents.")

if not documents:
    raise RuntimeError(
        f"No documents found in {DOCS_DIR}. "
        "Make sure doc_01.txt to doc_08.txt are inside support_assistant/docs/"
    )

# Generate embeddings
print("Generating embeddings...")
embeddings = model.encode(documents).tolist()

# Store in ChromaDB
print("Storing documents in ChromaDB...")

collection.upsert(
    ids=ids,
    documents=documents,
    embeddings=embeddings,
    metadatas=metadatas,
)

print(f"Successfully ingested {len(documents)} documents.")
print(f"ChromaDB location: {DB_DIR}")