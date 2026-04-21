# Backend Implementation Specifications (Claude Code)

> **Context:** This directory contains the backend for a RAG-based AI Study Assistant. A beautiful Next.js frontend has already been built that expects these APIs to function gracefully. The goal is to build a robust, scalable backend in Python using FastAPI.

## 🎯 Architecture & Stack Requirements

- **API Framework:** `FastAPI` (Python 3.11+)
- **Vector Database:** `Qdrant` (or `Pinecone`) for fast dense vector retrieval. 
- **Relational Database:** `PostgreSQL` (Use `SQLAlchemy` ORM) to store users, conversation logs, and quiz stats.
- **Short-Term Memory / Queue:** `Redis` (Use for chat history and Celery task queuing).
- **LLM / Generation:** `Groq` (e.g., `llama3-8b-8192` for fast response).
- **Embeddings:** `Sentence-Transformers` (e.g., `all-MiniLM-L6-v2` locally).
- **Document Parsing:** `PyMuPDF` or `Unstructured.io`.

---

## 🛑 PENDING FIXES FOR CLAUDE (As of latest review)
1. **Chat History Memory:** You are querying PostgreSQL for the chat session context window in `chat.py`. Please refactor this to use **Redis** short-term memory explicitly for active conversation streams to alleviate DB load.
2. **Celery Worker:** You currently use FastAPI's `BackgroundTasks` for PDF parsing. Please establish a proper **Celery** background worker using Redis as the message broker for genuine scalability.

---

## 🚦 Required Endpoints

You must construct the following endpoints. They must align with the mock data currently driving the UI.

### 1. `POST /api/documents/upload`
- **Action:** Accepts a multipart file (PDF/DOCX).
- **Flow:** 
  1. Save file to cloud/local storage.
  2. Emit background task (Celery) to parse the document using structure-aware chunking (keeping tables intact, 512-1024 token chunks).
  3. Generate embeddings and store them in the Vector DB with metadata: `[docId, userId, page_number]`.
- **Response:** Returns `{ status: "processing", docId: "UUID" }` immediately while the background task finishes.

### 2. `GET /api/documents`
- **Action:** Retrieves all documents for a user, indicating whether they are `"Processing"` or `"Ready"`.

### 3. `POST /api/chat`
- **Action:** Primary RAG loop.
- **Payload:** `{ query: "Explain cellular respiration", documentIds: ["UUID1"] }`
- **Flow:**
  1. **Query Rewriting:** Pull last 5 messages from Redis to convert follow-up pronouns to standalone queries.
  2. **Vector Search:** Fetch Top-15 from Vector DB.
  3. **Reranker:** Re-score with a Cross-Encoder to find the precise Top-5.
  4. **Confidence Guardrail:** If similarity is too low, reject immediately (prevent hallucinations).
  5. **Generation:** Instruct LLM strictly to use context, and return citations correlating to `docId` and `page_number`.
- **Response:** Needs to aggressively stream response tokens (SSE/WebSocket), or return JSON containing the text AND a `sources` array: `[{ page: 12, docId: "UUID", docName: "Biology" }]`.

### 4. `GET /api/quiz/generate`
- **Action:** Creates an active-recall quiz based on uploaded files.
- **Payload:** `{ documentIds: [...] }`
- **Flow:** LLM reads random chunks and synthesizes a JSON array containing `{ question, options, correctAnswer }`.

### 5. `GET /api/progress`
- **Action:** Fetches the mock analytics from PostgreSQL. Calculate user weak topics based on failed quiz questions.

---

## 🛠️ Key Technical Imperatives

1. **Anti-Hallucination:** System Prompts MUST instruct the LLM: *"If the answer is not contained precisely within the context below, output strictly: 'I cannot answer this based on the uploaded documents'."*
2. **Streaming:** Ensure Claude Code builds the `/chat` endpoint with asynchronous Python streaming so the UI feels fast.
3. **Background Workers:** Do not synchronously parse 50-page PDFs inside the `/upload` API route. Use Celery or FastAPI `BackgroundTasks`.

Claude, please scaffold out this FastAPI framework, database models, and the core routing infrastructure. Use clean `.env` file management for API keys.
