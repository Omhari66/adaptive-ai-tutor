# RAG Study Assistant - Backend

FastAPI-based backend for the AI Study Assistant with RAG (Retrieval-Augmented Generation) capabilities.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      FastAPI Backend                         │
├─────────────────────────────────────────────────────────────┤
│  API Routes                                                 │
│  ├── /api/documents  - Document upload & management         │
│  ├── /api/chat       - RAG-powered chat                     │
│  ├── /api/quiz       - Quiz generation                      │
│  └── /api/progress   - Analytics & progress tracking        │
├─────────────────────────────────────────────────────────────┤
│  Services                                                   │
│  ├── RAG Service     - Query rewriting, retrieval, ranking  │
│  ├── Document Service - PDF/DOCX parsing, chunking          │
│  └── Quiz Service    - LLM-based quiz generation            │
└─────────────────────────────────────────────────────────────┘
                          │
        ┌─────────────────┼─────────────────┐
        │                 │                 │
        ▼                 ▼                 ▼
   ┌─────────┐      ┌──────────┐     ┌──────────┐
   │PostgreSQL│      │  Qdrant  │     │  Redis   │
   │(Relational)│     │(Vectors) │     │ (Cache)  │
   └─────────┘      └──────────┘     └──────────┘
```

## Quick Start

### Prerequisites

- Python 3.11+
- PostgreSQL 14+
- Qdrant vector database
- Redis (optional, for caching)
- Groq API key

### Installation

1. **Clone and navigate to backend:**
   ```bash
   cd backend
   ```

2. **Create virtual environment:**
   ```bash
   python -m venv venv

   # Windows
   venv\Scripts\activate

   # Linux/Mac
   source venv/bin/activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment:**
   Copy `.env.example` to `.env` and update:
   ```bash
   cp .env.example .env
   ```

   Required configurations:
   - `GROQ_API_KEY` - Your Groq API key
   - `DATABASE_URL` - PostgreSQL connection string
   - `QDRANT_URL` - Qdrant vector database URL

5. **Start the server:**
   ```bash
   # Windows
   start.bat

   # Linux/Mac
   chmod +x start.sh
   ./start.sh
   ```

   Or manually:
   ```bash
   uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
   ```

## API Endpoints

### Documents

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/documents/upload` | Upload PDF/DOCX/TXT file |
| GET | `/api/documents` | List all documents |
| DELETE | `/api/documents/{id}` | Delete a document |

### Chat

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/chat` | Send message and get RAG response |
| GET | `/api/chat/sessions` | List chat sessions |
| DELETE | `/api/chat/sessions/{id}` | Delete a session |

### Quiz

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/quiz/generate` | Generate quiz from documents |
| POST | `/api/quiz/submit` | Submit quiz answers |
| GET | `/api/quiz/results` | Get quiz history |

### Progress

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/progress` | Get user analytics |
| GET | `/api/progress/recent-activity` | Recent activity |

## API Documentation

Once running, access interactive API docs at:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## RAG Pipeline

The chat endpoint implements a sophisticated RAG pipeline:

1. **Query Rewriting**: Uses LLM to convert follow-up questions into standalone queries
2. **Vector Search**: Retrieves top-15 relevant chunks from Qdrant
3. **Reranking**: Cross-encoder reranks to find top-5 most relevant
4. **Confidence Check**: Rejects low-confidence results to prevent hallucinations
5. **LLM Generation**: Generates response with strict citation requirements

## Document Processing

Uploaded documents go through:

1. **Parsing**: PyMuPDF (PDF) or python-docx (DOCX) extracts text
2. **Chunking**: Structure-aware chunking (512 tokens, 50 overlap)
3. **Embedding**: Local `sentence-transformers` embeddings generated for each chunk
4. **Vector Storage**: Chunks stored in Qdrant with metadata

## Database Schema

### Tables

- `users` - User accounts
- `documents` - Uploaded file metadata
- `document_chunks` - Text chunks and embedding references
- `chat_sessions` - Chat conversation groups
- `chat_messages` - Individual chat messages
- `quizzes` - Generated quizzes
- `quiz_questions` - Quiz questions
- `quiz_results` - User quiz performance

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `GROQ_API_KEY` | Groq API key | - |
| `GROQ_MODEL` | LLM model | `llama3-8b-8192` |
| `EMBEDDING_MODEL` | Embedding model | `text-embedding-3-large` |
| `DATABASE_URL` | PostgreSQL URL | `postgresql://...` |
| `QDRANT_URL` | Qdrant URL | `http://localhost:6333` |
| `REDIS_URL` | Redis URL | `redis://localhost:6379/0` |
| `VECTOR_SEARCH_TOP_K` | Vector search results | `15` |
| `RERANK_TOP_K` | Reranked results | `5` |
| `CHUNK_SIZE` | Token chunk size | `512` |
| `CONFIDENCE_THRESHOLD` | Min similarity score | `0.3` |

## Development

### Running Tests

```bash
pytest
```

### Code Style

```bash
# Format code
black app/

# Lint code
flake8 app/
```

## Troubleshooting

### "Qdrant connection failed"
- Ensure Qdrant is running: `docker run -p 6333:6333 qdrant/qdrant`

### "Database connection failed"
- Check PostgreSQL is running
- Verify `DATABASE_URL` in `.env`

### "Groq API error"
- Verify `GROQ_API_KEY` is set correctly
- Check API key has sufficient credits

## License

MIT
