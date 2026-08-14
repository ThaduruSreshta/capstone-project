# Zepto Support Assistant

## Overview

This project implements an offline customer-support assistant for Zepto using a Retrieval-Augmented Generation (RAG) architecture.

The system retrieves relevant information from a local collection of support-policy documents and generates a concise response based only on the retrieved context.

## Features

* Offline document retrieval using ChromaDB
* Semantic search using the `all-MiniLM-L6-v2` embedding model
* LangGraph-based query routing
* FastAPI REST API
* Structured request and response validation using Pydantic
* Source document IDs returned with answers
* Confidence score included in API responses
* Mock/deterministic answer generation without requiring an external LLM API
* Docker support

## Project Structure

```text
support_assistant/
├── docs/
│   ├── doc_01.txt
│   ├── doc_02.txt
│   ├── doc_03.txt
│   ├── doc_04.txt
│   ├── doc_05.txt
│   ├── doc_06.txt
│   ├── doc_07.txt
│   └── doc_08.txt
├── chroma_db/
├── ingest.py
├── main.py
├── requirements.txt
├── Dockerfile
└── README.md
```

## Architecture

The application follows this flow:

```text
User Query
    ↓
FastAPI /ask endpoint
    ↓
LangGraph
    ↓
Intent Classification
    ↓
 ┌───────────────────────┐
 │                       │
Policy Question      General Question
 │                       │
 ↓                       ↓
ChromaDB Retrieval   Direct Response
 │
 ↓
Top Relevant Documents
 │
 ↓
Concise Answer + Sources
```

## Components

### 1. Document Ingestion

`ingest.py` reads the support documents from the `docs/` directory and generates embeddings using:

`all-MiniLM-L6-v2`

The documents and their embeddings are stored in a persistent local ChromaDB collection named `support_docs`.

### 2. Retrieval

For a policy-related query, `main.py` generates an embedding for the query and retrieves the top three relevant documents from ChromaDB using semantic similarity.

### 3. Intent Classification

The LangGraph workflow first classifies the query.

Policy-related keywords include:

* delivery
* return
* refund
* membership
* tracking
* cancel
* gift card
* support hours

Policy questions are routed to document retrieval. General questions receive a controlled response indicating that the assistant currently answers Zepto policy questions.

### 4. Answer Generation

The baseline implementation uses deterministic mock-mode responses.

The answer is generated from the retrieved context and does not require an external LLM API.

If relevant information cannot be retrieved, the system returns a controlled response rather than inventing information.

## API

### GET `/`

Health/status endpoint.

Example response:

```json
{
  "message": "Zepto Support Assistant is running"
}
```

### POST `/ask`

Accepts a customer-support query.

Request:

```json
{
  "query": "How long does delivery take?"
}
```

Response structure:

```json
{
  "answer": "Based on the retrieved context: ...",
  "sources": ["doc_01"],
  "confidence": 1.0
}
```

## Running Locally

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Start the API

From the `support_assistant` directory:

```bash
uvicorn main:app --reload
```

### 3. Open API documentation

Open:

```text
http://127.0.0.1:8000/docs
```

The interactive Swagger UI can be used to test the API.

## Rebuilding the ChromaDB

If the document collection needs to be recreated or updated:

```bash
python ingest.py
```

This reads the files from `docs/` and stores their embeddings in the local `chroma_db/` directory.

## Docker

A `Dockerfile` is included to containerize the support assistant.

Build the image:

```bash
docker build -t zepto-support-assistant .
```

Run the container:

```bash
docker run -p 8000:8000 zepto-support-assistant
```

The API can then be accessed at:

```text
http://127.0.0.1:8000/docs
```

## Technologies Used

* Python
* FastAPI
* ChromaDB
* Sentence Transformers
* LangGraph
* Pydantic
* Uvicorn
* Docker

## Limitations

* The baseline uses deterministic mock responses rather than an external generative LLM.
* The assistant is restricted to the supplied Zepto policy context.
* Query classification currently uses a keyword-based approach.
* The embedding model is downloaded locally and used for semantic retrieval.

## Conclusion

The project demonstrates an end-to-end offline RAG support-assistant pipeline consisting of document ingestion, semantic retrieval, intent routing, controlled response generation, source tracking, and REST API deployment.
