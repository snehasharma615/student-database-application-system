# Vector Database Research and Selection

## Requirement

The internship project requires research and selection of a suitable vector database.

## Options considered

### 1. ChromaDB
- Python-friendly
- Simple local persistent mode
- Stores documents and embeddings
- Supports semantic similarity queries
- Easy to demonstrate in a student capstone
- Can later be moved to server/client deployment

### 2. FAISS
- Very strong similarity-search library
- Lightweight and fast
- Excellent for local vector indexing
- More responsibility is left to the application for metadata/storage and persistence design

### 3. Pinecone
- Managed vector database service
- Good fit for production cloud systems
- Requires an external account/service and API configuration

### 4. Weaviate
- Full vector database platform
- Supports richer cloud/self-hosted deployments
- More infrastructure than needed for this local capstone

## Selected database: ChromaDB

ChromaDB is selected for this project because it provides a simple persistent local client, a straightforward collection API, document storage, embedding/indexing support and semantic querying. This keeps the capstone easy to run while still demonstrating a real vector database workflow.

The application stores student-related knowledge text in a Chroma collection and retrieves semantically relevant documents for the LangGraph chatbot.

## Where ChromaDB is used

```text
Knowledge documents
       |
       v
Chroma collection
       |
       v
semantic query
       |
       v
top matching documents
       |
       v
Gemini answer generation
```

## Important distinction

ChromaDB is not used as a replacement for SQLite.

- SQLite = structured student records and CRUD.
- ChromaDB = semantic retrieval of unstructured knowledge.
- LangGraph = workflow orchestration.
- Gemini = natural-language understanding and response generation.

This separation demonstrates why both a relational database and a vector database can coexist in an AI application.


## What is a vector database?

A vector database stores vector representations of text or other data and supports similarity search. In this project, text documents are embedded and queried by semantic similarity so that a question can retrieve relevant project knowledge even when the wording is not an exact keyword match.

## Comparison

| Option | Strength | Trade-off | Fit |
|---|---|---|---|
| ChromaDB | Simple Python API, local persistence, document metadata | Local deployment needs persistent storage for durable cloud data | Selected |
| FAISS | Fast similarity search library | More application code is needed for metadata and persistence | Good |
| Pinecone | Managed cloud vector service | External account and service configuration | Production-oriented |
| Weaviate | Full vector database platform | More infrastructure/configuration | Larger deployments |

## ChromaDB limitations

ChromaDB local persistent mode is convenient for a capstone but is not equivalent to a managed production vector service. Cloud deployments using an ephemeral filesystem can lose local vector data after restart or redeploy. The embedding model may also need to be downloaded on first use, so deployment requires suitable network access and resources.
