<p align="center">
  <img src="docs/images/banner.png" alt="AdaptIQ Banner" width="100%"/>
</p>

<p align="center">
  <strong>An AI-powered study assistant that reads your documents, teaches adaptively, and tracks your learning progress.</strong>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Next.js-16-black?logo=next.js" alt="Next.js"/>
  <img src="https://img.shields.io/badge/FastAPI-0.115-009688?logo=fastapi" alt="FastAPI"/>
  <img src="https://img.shields.io/badge/PostgreSQL-15-336791?logo=postgresql" alt="PostgreSQL"/>
  <img src="https://img.shields.io/badge/Qdrant-1.8-dc382d?logo=data:image/svg+xml;base64," alt="Qdrant"/>
  <img src="https://img.shields.io/badge/Groq-LLaMA_3.1-f55036" alt="Groq"/>
  <img src="https://img.shields.io/badge/Docker-Compose-2496ED?logo=docker" alt="Docker"/>
  <img src="https://img.shields.io/badge/License-MIT-green" alt="License"/>
</p>

---

## 🧠 What is AdaptIQ?

AdaptIQ is a full-stack **Retrieval-Augmented Generation (RAG)** study assistant that lets you upload textbooks, lecture notes, or any study material — then learn from them through an intelligent AI tutor that adapts to your understanding level.

Unlike generic chatbots, AdaptIQ:
- **Grounds every answer in your documents** with page-level citations — no hallucinations
- **Adapts its teaching format** based on content type (math → step-by-step, theory → conceptual, comparisons → tables)
- **Tracks your confidence** per topic and suggests when to switch study modes
- **Generates quizzes** automatically and adjusts difficulty based on your performance

---

## ✨ Features

### 🎓 4 Adaptive Learning Modes

| Mode | Purpose | How it works |
|------|---------|-------------|
| **💬 Normal** | Planning & onboarding | Casual chat, study planning, app guidance — no documents used |
| **📖 Teacher** | Deep conceptual learning | Adaptive formatting: detects math/theory/procedure/comparison and uses the best explanation structure |
| **⚡ Revision** | Rapid review | Compressed key points, formulas, and memory tricks — optimized for retention |
| **🧪 Exam** | Self-testing | Bloom's Taxonomy questions with auto-difficulty scaling and detailed feedback |

### 📊 Intelligent Learning Engine
- **Per-topic confidence scoring** with 5% memory decay over time
- **Automatic weak-topic detection** to focus your study time
- **Smart mode suggestions** — struggling? → Revision. Acing it? → Exam mode
- **Rolling performance windows** for adaptive difficulty in Exam mode

### 🔍 Production RAG Pipeline
- PDF/DOCX/TXT document parsing with semantic chunking (512 tokens)
- Local embeddings via `all-MiniLM-L6-v2` (384-dim, zero API cost)
- Qdrant vector search with cosine similarity
- Cross-encoder reranking for precision
- Real-time token streaming via Server-Sent Events (SSE)
- Page-level source citations on every answer

### 📝 Auto-Generated Quizzes
- Multiple question types generated from your documents
- Score tracking and performance analytics
- Visual progress dashboard with Recharts

---

## 🏗️ Architecture

<p align="center">
  <img src="docs/images/architecture.png" alt="System Architecture" width="85%"/>
</p>

### RAG Pipeline Flow

```
User Question
    │
    ▼
┌─────────────────┐
│  Query Rewriter  │ ← Conversation context (last 5 msgs)
└────────┬────────┘
         ▼
┌─────────────────┐
│  Embedding Gen   │ ← all-MiniLM-L6-v2 (384-dim)
└────────┬────────┘
         ▼
┌─────────────────┐
│  Qdrant Search   │ ← Cosine similarity, top-K retrieval
└────────┬────────┘
         ▼
┌─────────────────┐
│  Cross-Encoder   │ ← Reranking for precision (top-5 → top-3)
│    Reranker      │
└────────┬────────┘
         ▼
┌─────────────────┐
│   Groq LLM      │ ← Mode-specific prompt + context + guardrails
│  (LLaMA 3.1)    │
└────────┬────────┘
         ▼
   Streamed Response with Citations
```

---

## 🛠️ Tech Stack

| Layer | Technology |
|-------|-----------|
| **Frontend** | Next.js 16, React 19, TypeScript, TailwindCSS v4 |
| **Backend** | FastAPI, Python 3.11+, SQLAlchemy ORM |
| **LLM** | Groq API (LLaMA 3.1 8B Instant) |
| **Embeddings** | Sentence-Transformers (all-MiniLM-L6-v2) |
| **Vector DB** | Qdrant v1.8 (cosine similarity, 384-dim) |
| **Relational DB** | PostgreSQL 15 / SQLite (dev) |
| **Task Queue** | Redis 7 + Celery (async document processing) |
| **Auth** | JWT (PyJWT + passlib/bcrypt) |
| **Streaming** | Server-Sent Events (SSE) |
| **Containerization** | Docker Compose |

---

## 🚀 Getting Started

### Prerequisites

- **Node.js** 18+ and **npm**
- **Python** 3.11+
- **Docker** (for PostgreSQL, Redis, Qdrant) — or use SQLite for quick dev setup
- **Groq API Key** — [Get one free](https://console.groq.com/keys)

### Quick Start (Development)

```bash
# 1. Clone the repository
git clone https://github.com/yourusername/adaptiq.git
cd adaptiq

# 2. Start infrastructure services
docker-compose up -d

# 3. Setup backend
cd backend
python -m venv venv
venv\Scripts\activate          # Windows
# source venv/bin/activate     # macOS/Linux
pip install -r requirements.txt

# 4. Configure environment
cp .env.example .env
# Edit .env and add your GROQ_API_KEY

# 5. Run database migrations
python migrate.py

# 6. Start backend server
uvicorn app.main:app --reload

# 7. Setup frontend (new terminal)
cd ..
npm install
npm run dev
```

### Quick Start (One Command — Windows)

```bash
start.bat
```

### Environment Variables

Create a `backend/.env` file:

```env
# Required
GROQ_API_KEY=your_groq_api_key_here

# Database (use SQLite for quick dev, PostgreSQL for production)
DATABASE_URL=sqlite:///./rag.db
# DATABASE_URL=postgresql://postgres:password@localhost:5432/rag_study_assistant

# Vector Database
QDRANT_URL=local
# QDRANT_URL=http://localhost:6333

# Auth
JWT_SECRET=your-secret-key-here

# Optional
GROQ_MODEL=llama-3.1-8b-instant
EMBEDDING_MODEL=all-MiniLM-L6-v2
```

---

## 📁 Project Structure

```
adaptiq/
├── app/                          # Next.js frontend pages
│   ├── chat/                     # Main chat interface
│   ├── documents/                # Document management
│   ├── quiz/                     # Quiz interface
│   ├── progress/                 # Learning analytics dashboard
│   ├── login/                    # Authentication
│   ├── register/                 # User registration
│   └── settings/                 # User settings
│
├── components/                   # React components
│   ├── chat/
│   │   ├── ChatInput.tsx         # Input with mode-specific prompt chips
│   │   └── ChatMessage.tsx       # Message renderer with citations
│   └── layout/
│       └── Sidebar.tsx           # Navigation sidebar
│
├── lib/
│   └── api.ts                    # Frontend API client
│
├── backend/
│   ├── app/
│   │   ├── api/routes/
│   │   │   ├── auth.py           # JWT authentication endpoints
│   │   │   ├── chat.py           # Chat + SSE streaming endpoint
│   │   │   ├── documents.py      # Document upload & management
│   │   │   ├── quiz.py           # Quiz generation & scoring
│   │   │   ├── exam.py           # Exam mode endpoints
│   │   │   └── progress.py       # Learning analytics API
│   │   │
│   │   ├── core/
│   │   │   ├── config.py         # Pydantic settings
│   │   │   ├── database.py       # SQLAlchemy setup
│   │   │   ├── auth.py           # JWT middleware
│   │   │   └── prompts.py        # Mode-specific system prompts
│   │   │
│   │   ├── models/               # SQLAlchemy ORM models
│   │   │   ├── user.py
│   │   │   ├── chat.py
│   │   │   ├── document.py
│   │   │   ├── quiz.py
│   │   │   └── learning_state.py
│   │   │
│   │   ├── services/             # Business logic
│   │   │   ├── rag_service.py          # Full RAG pipeline
│   │   │   ├── embedding_service.py    # Sentence-transformer embeddings
│   │   │   ├── document_service.py     # PDF/DOCX parsing + chunking
│   │   │   ├── evaluation_service.py   # Answer evaluation
│   │   │   ├── learning_state_service.py # Confidence tracking
│   │   │   ├── topic_service.py        # Topic detection
│   │   │   ├── quiz_service.py         # Quiz generation
│   │   │   └── exam_mode_service.py    # Exam mode logic
│   │   │
│   │   └── main.py               # FastAPI application entry
│   │
│   ├── requirements.txt
│   └── migrate.py                # Database migration script
│
├── docker-compose.yml            # PostgreSQL, Redis, Qdrant
└── start.bat                     # One-click launcher (Windows)
```

---

## 🔌 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/auth/register` | User registration |
| `POST` | `/api/auth/login` | JWT login |
| `POST` | `/api/chat` | Chat with RAG (supports SSE streaming) |
| `GET` | `/api/chat/sessions` | List chat sessions |
| `GET` | `/api/chat/{id}/messages` | Get session messages |
| `POST` | `/api/documents/upload` | Upload PDF/DOCX/TXT |
| `GET` | `/api/documents` | List user documents |
| `POST` | `/api/quiz/generate` | Generate quiz from documents |
| `POST` | `/api/quiz/submit` | Submit quiz answers |
| `GET` | `/api/progress/overview` | Learning analytics |
| `GET` | `/api/progress/confidence` | Per-topic confidence scores |

Full interactive docs available at `http://localhost:8000/docs` (Swagger UI)

---

## 📊 Key Metrics

| Metric | Value |
|--------|-------|
| Embedding dimensions | 384 |
| Chunk size | 512 tokens |
| Chunk overlap | 50 tokens |
| Vector search top-K | 5 |
| Rerank top-K | 3 |
| Confidence threshold | 0.3 |
| Context window | Last 5 messages |
| Time-to-first-token | ~100ms |

---

## 🤝 Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## 📜 License

Distributed under the MIT License. See `LICENSE` for more information.

---

## 🙏 Acknowledgements

- [Groq](https://groq.com/) — Ultra-fast LLM inference
- [Qdrant](https://qdrant.tech/) — Vector similarity search
- [Sentence-Transformers](https://sbert.net/) — Local embeddings
- [FastAPI](https://fastapi.tiangolo.com/) — Modern Python API framework
- [Next.js](https://nextjs.org/) — React framework for production

---

<p align="center">
  Built with ❤️ for smarter studying
</p>
