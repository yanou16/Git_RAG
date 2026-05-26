---
title: GitRAG API
emoji: 🔍
colorFrom: indigo
colorTo: purple
sdk: docker
pinned: false
license: mit
app_port: 7860
---

# GitRAG

**Ask natural-language questions about any public GitHub repository — and get answers grounded in actual source code, with exact file paths and line numbers.**

[![CI/CD](https://github.com/yanou16/Git_RAG/actions/workflows/ci.yml/badge.svg)](https://github.com/yanou16/Git_RAG/actions/workflows/ci.yml)
[![Python 3.13](https://img.shields.io/badge/python-3.13-blue.svg)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

**Live demo:** [gitrag.vercel.app](https://gitrag.vercel.app) &nbsp;·&nbsp; **API:** [yanou16-gitgub-rag.hf.space](https://yanou16-gitgub-rag.hf.space/docs)

---

## How it works

```
GitHub repo
    │
    ▼
AST-aware chunking          — splits files into semantic units (functions, classes)
    │
    ▼
Embeddings (text-embedding-3-small) + BM25 index
    │
    ▼
Hybrid retrieval (semantic + BM25 → Reciprocal Rank Fusion)
    │
    ▼
Cohere reranking            — cross-encoder rescores top 20 → keeps best 5
    │
    ▼
Groq llama-3.3-70b          — generates a grounded answer with file citations
```

**Supported languages:** Python, JavaScript/TypeScript, C#, Java, C/C++, Go, Rust, Ruby, PHP, Swift, Kotlin, Dart, Vue, Svelte, Shell, SQL, HTML, CSS, JSON, YAML, TOML, XML

---

## Project structure

```
gitrag/
├── app/                        # FastAPI backend
│   ├── main.py                 # App entry point, middleware, CORS
│   ├── config.py               # Settings via environment variables
│   ├── routes/
│   │   ├── ingest.py           # POST /ingest — clone, chunk, embed, store
│   │   ├── query.py            # POST /query  — hybrid search + rerank + LLM
│   │   └── health.py           # GET  /health — liveness check
│   ├── services/
│   │   ├── github.py           # GitHub API client (file listing + content fetch)
│   │   ├── chunker.py          # AST-aware code chunking
│   │   ├── embedder.py         # OpenAI-compatible embedding service
│   │   ├── vector_store.py     # ChromaDB wrapper (upsert, similarity search)
│   │   ├── hybrid_search.py    # BM25 + semantic → RRF fusion
│   │   ├── reranker.py         # Cohere reranking
│   │   └── llm.py              # Groq LLM answer generation
│   ├── models/
│   │   └── schemas.py          # Pydantic request/response models
│   └── utils/
│       ├── hashing.py          # URL → stable repo_id
│       └── retry.py            # Async retry decorator
├── frontend/                   # React + Vite frontend (deployed on Vercel)
│   ├── src/
│   │   ├── components/         # Navbar, Hero, HowItWorks, Tool, Footer
│   │   ├── api.js              # API client (ingestRepo, queryRepo)
│   │   └── App.jsx
│   ├── tailwind.config.cjs
│   └── vite.config.js
├── tests/                      # pytest integration tests (40 tests)
├── Dockerfile                  # Production image for HuggingFace Spaces
├── docker-compose.yml          # Local dev with Docker
└── requirements.txt
```

---

## Quick start

### Prerequisites

- Python 3.13+
- API keys: OpenAI-compatible embeddings, Groq, Cohere (optional)

### Run locally

```bash
git clone https://github.com/yanou16/Git_RAG.git
cd Git_RAG

# Backend
cp .env.example .env        # fill in your API keys
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000

# Frontend (separate terminal)
cd frontend
npm install
npm run dev                  # http://localhost:3000
```

### Run with Docker

```bash
docker compose up --build
```

---

## API reference

### `POST /ingest`

Index a public GitHub repository.

```json
{
  "repo_url": "https://github.com/tiangolo/fastapi",
  "branch": "master",
  "force_reindex": false
}
```

**Response:**
```json
{
  "repo_id": "abc123",
  "files_indexed": 87,
  "chunks_stored": 1243,
  "duration_ms": 18420,
  "was_cached": false
}
```

### `POST /query`

Ask a question about an indexed repository.

```json
{
  "repo_url": "https://github.com/tiangolo/fastapi",
  "question": "How does dependency injection work?",
  "use_hybrid": true,
  "use_reranking": true
}
```

**Response:**
```json
{
  "answer": "Dependency injection in FastAPI works via...",
  "sources": [
    {
      "file_path": "fastapi/dependencies/utils.py",
      "start_line": 145,
      "excerpt": "...",
      "rerank_score": 0.92
    }
  ],
  "pipeline": "hybrid+rerank",
  "tokens_used": 1247,
  "latency_ms": 1834
}
```

### `GET /health`

```json
{ "status": "ok", "version": "1.0.0" }
```

---

## Deployment

### Backend — HuggingFace Spaces (Docker)

1. Fork this repo
2. Create a Space at [huggingface.co/spaces](https://huggingface.co/spaces) with **Docker** SDK
3. Add your HF Space as a git remote: `git remote add hf https://huggingface.co/spaces/<user>/<space>`
4. Set secrets in Space Settings:

| Secret | Description |
|--------|-------------|
| `ANIMUSAI_API_KEY` | OpenAI-compatible key for `text-embedding-3-small` |
| `ANIMUSAI_BASE_URL` | e.g. `https://api.openai.com/v1` |
| `GROQ_API_KEY` | [console.groq.com](https://console.groq.com) |
| `COHERE_API_KEY` | Optional — enables reranking |
| `GITHUB_TOKEN` | Optional — raises rate limit from 60 to 5000 req/h |

5. Push: `git push hf main`

### Frontend — Vercel

1. Import the repo on [vercel.com](https://vercel.com)
2. Set **Root Directory** to `frontend`
3. Add env var: `VITE_API_URL=https://<your-space>.hf.space`
4. Deploy

---

## Tests

```bash
pip install -r requirements-dev.txt
pytest tests/ -v
```

40 integration tests covering ingest, query, chunking, hybrid search, and health endpoints.

---

## Tech stack

| Layer | Technology |
|-------|-----------|
| API | FastAPI + Uvicorn |
| Embeddings | OpenAI `text-embedding-3-small` |
| Vector store | ChromaDB (persistent) |
| Keyword search | BM25 (rank-bm25) |
| Fusion | Reciprocal Rank Fusion |
| Reranking | Cohere `rerank-v3.5` |
| LLM | Groq `llama-3.3-70b-versatile` |
| Frontend | React + Vite + Tailwind CSS |
| Hosting | HuggingFace Spaces (backend) + Vercel (frontend) |

---

## Author

**Rayane Louzazna** — [LinkedIn](https://www.linkedin.com/in/rayane-louzazna-b7752b224) · [GitHub](https://github.com/yanou16)

MIT License
