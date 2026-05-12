# GitRAG — GitHub Codebase Q&A via RAG

[![CI/CD](https://github.com/yanou16/gitrag/actions/workflows/ci.yml/badge.svg)](https://github.com/yanou16/gitrag/actions/workflows/ci.yml)
[![Python 3.13](https://img.shields.io/badge/python-3.13-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.111+-green.svg)](https://fastapi.tiangolo.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

> Ask natural-language questions about any public GitHub repository — and get answers grounded in the actual source code, with exact file paths and line numbers.

**Live API:** `https://yanou16-gitrag.hf.space`
**Frontend:** `https://gitrag.streamlit.app`

---

## Table of Contents

1. [What it does](#what-it-does)
2. [Architecture](#architecture)
3. [Quick Start](#quick-start)
4. [API Reference](#api-reference)
5. [The RAG Pipeline](#the-rag-pipeline)
6. [Chunking Strategy](#chunking-strategy)
7. [Engineering Decisions](#engineering-decisions)
8. [Why NOT LangChain](#why-not-langchain)
9. [Resilience & Fallbacks](#resilience--fallbacks)
10. [Limitations](#limitations)
11. [Deployment](#deployment)
12. [Development](#development)

---

## What it does

GitRAG turns any public GitHub repository into a queryable knowledge base in two API calls:

1. **`POST /ingest`** — fetches the repo via GitHub API, chunks code by its AST structure (one function = one chunk), embeds each chunk into a 1536-dimensional vector, and stores everything in ChromaDB.
2. **`POST /query`** — embeds your question, runs a hybrid search (semantic cosine similarity + BM25 keyword), optionally reranks results with Cohere, and sends the top chunks to a Groq LLM to generate a grounded answer.

No hallucination about code that isn't there — every claim in the answer is traceable to a source chunk with file path + line numbers.

---

## Architecture

```
┌──────────────────────────────────────────────────────────────┐
│                  Client (Streamlit / curl)                    │
└──────────────────────┬───────────────────────────────────────┘
                       │ HTTP
┌──────────────────────▼───────────────────────────────────────┐
│                    FastAPI  (app/main.py)                      │
│                                                               │
│  POST /ingest                      POST /query                │
│  ┌─────────────────────┐          ┌───────────────────────┐   │
│  │ 1. GitHub API       │          │ 1. Embed question      │   │
│  │ 2. AST Chunking     │          │ 2. Semantic search     │   │
│  │ 3. Embed chunks     │          │ 3. BM25 hybrid (RRF)   │   │
│  │ 4. Store ChromaDB   │          │ 4. Cohere rerank       │   │
│  └─────────────────────┘          │ 5. Groq LLM answer     │   │
│                                   └───────────────────────┘   │
└──────────┬────────────────────────────────┬───────────────────┘
           │                                │
┌──────────▼──────────┐        ┌────────────▼────────────────┐
│  ChromaDB (HNSW)    │        │  External APIs              │
│  /app/chroma_data   │        │  • OpenAI text-embedding-   │
│  (Docker volume)    │        │    3-small (1536D)          │
└─────────────────────┘        │  • Cohere rerank-v3.5       │
                               │  • Groq llama-3.3-70b       │
                               └─────────────────────────────┘
```

**Stack:**

| Layer | Technology | Why |
|---|---|---|
| API framework | FastAPI | Async-native, auto OpenAPI docs, Pydantic validation |
| Vector DB | ChromaDB | Embedded, no infra cost, HNSW for fast ANN search |
| Embeddings | OpenAI `text-embedding-3-small` | Best price/quality at 1536D |
| Keyword search | BM25 (rank-bm25) | Catches exact terms semantic search misses |
| Fusion | RRF — Reciprocal Rank Fusion | Score-free combination, no weight tuning |
| Reranking | Cohere `rerank-english-v3.5` | Cross-encoder quality, optional |
| LLM | Groq `llama-3.3-70b-versatile` | ~200 tokens/s, free tier, 128K context |
| Logging | structlog | JSON-structured, correlatable logs |
| Containerization | Docker + Docker Compose | One-command deploy |

---

## Quick Start

### Option 1 — Docker (recommended)

```bash
# Clone
git clone https://github.com/yanou16/gitrag.git
cd gitrag

# Configure
cp .env.example .env
# Edit .env with your API keys (see below)

# Run
docker compose up --build
```

API is live at `http://localhost:8000`. Interactive docs at `http://localhost:8000/docs`.

### Option 2 — Local Python

```bash
python -m venv .venv
# Linux/Mac:
source .venv/bin/activate
# Windows:
.venv\Scripts\activate

pip install -r requirements.txt
cp .env.example .env   # fill in your keys
uvicorn app.main:app --reload
```

### Required environment variables

```ini
# Required
ANIMUSAI_API_KEY=sk-...            # OpenAI-compatible key for embeddings
ANIMUSAI_BASE_URL=https://api.openai.com/v1
GROQ_API_KEY=gsk_...               # Groq key — free at console.groq.com

# Optional — pipeline degrades gracefully without this
COHERE_API_KEY=...                 # Enables Cohere reranking step

# Tuning (defaults shown)
GROQ_MODEL=llama-3.3-70b-versatile
MAX_FILE_SIZE_KB=500
MAX_REPO_FILES=200
CHUNK_SIZE=40
CHUNK_OVERLAP=10
```

---

## API Reference

### `POST /ingest`

Index a GitHub repository.

```bash
curl -X POST http://localhost:8000/ingest \
  -H "Content-Type: application/json" \
  -d '{
    "repo_url": "https://github.com/tiangolo/fastapi",
    "branch": "master",
    "max_files": 100,
    "force_reindex": false
  }'
```

**Response:**

```json
{
  "repo_id": "abc123def456",
  "repo_url": "https://github.com/tiangolo/fastapi",
  "files_processed": 87,
  "chunks_indexed": 1204,
  "skipped_files": 3,
  "already_indexed": false,
  "message": "Successfully indexed 87 files (1204 chunks)"
}
```

---

### `POST /query`

Ask a question about an indexed repository.

```bash
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{
    "repo_url": "https://github.com/tiangolo/fastapi",
    "question": "How does dependency injection work?",
    "k": 5,
    "use_hybrid": true,
    "use_reranking": true
  }'
```

**Response:**

```json
{
  "answer": "FastAPI's dependency injection uses the `Depends()` function...",
  "sources": [
    {
      "file_path": "fastapi/dependencies/utils.py",
      "start_line": 42,
      "end_line": 89,
      "language": "python",
      "similarity_score": 0.8921,
      "rerank_score": 0.9740,
      "excerpt": "async def solve_dependencies(...) ..."
    }
  ],
  "repo_id": "abc123def456",
  "latency_ms": 1243.5,
  "tokens_used": 892,
  "model": "llama-3.3-70b-versatile",
  "k_retrieved": 5,
  "pipeline": "hybrid+rerank"
}
```

**Query parameters:**

| Field | Type | Default | Description |
|---|---|---|---|
| `repo_url` | string | required | Full GitHub URL |
| `question` | string | required | Min 3 chars |
| `k` | int | 5 | Number of chunks in the final answer (1–20) |
| `use_hybrid` | bool | true | Enable BM25 + RRF fusion |
| `use_reranking` | bool | true | Enable Cohere reranking |
| `language` | string | null | Filter by language (python, typescript…) |
| `temperature` | float | 0.1 | LLM temperature |

---

### `DELETE /ingest/{repo_url}`

Remove a repo from the index.

```bash
curl -X DELETE "http://localhost:8000/ingest/https%3A%2F%2Fgithub.com%2Ftiangolo%2Ffastapi"
```

---

### `GET /health`

```bash
curl http://localhost:8000/health
# {"status":"healthy","version":"1.0.0","total_queries":42,"avg_latency_ms":980.3}
```

---

## The RAG Pipeline

RAG stands for **Retrieval-Augmented Generation**. Instead of asking an LLM to hallucinate code details from its training data, we:

1. **Retrieve** the most relevant code chunks from the actual repository
2. **Augment** the LLM prompt with those chunks as context
3. **Generate** an answer grounded only in what was retrieved

Here is what happens on every `POST /query`:

```
Question
   │
   ▼
[1] EMBED QUESTION
    text-embedding-3-small → float[1536]
    Same model used to embed chunks at ingest time → same vector space
   │
   ▼
[2] SEMANTIC SEARCH  (k × 4 candidates)
    ChromaDB HNSW cosine similarity
    We fetch 4× more candidates than requested — wide net for the reranker
   │
   ▼
[3] BM25 KEYWORD SEARCH  (if use_hybrid=true)
    rank-bm25 scores each candidate for exact term matches
    Catches things like "JWT_TOKEN" or "calculate_shipping" that semantic
    search misses because the query phrasing differs
   │
   ▼
[4] RECIPROCAL RANK FUSION
    score(chunk) = 1/(k+rank_semantic) + 1/(k+rank_bm25)   k=60 (Cormack 2009)
    Merges the two ranked lists without needing to tune weights.
    Chunks appearing high in BOTH lists float to the top.
   │
   ▼
[5] COHERE RERANKING  (if use_reranking=true and COHERE_API_KEY set)
    Sends (question, chunk_text) pairs to Cohere rerank-english-v3.5.
    Cross-encoder: sees the question AND the chunk together, giving a
    true relevance score instead of an approximation.
    Selects final k chunks.
   │
   ▼
[6] LLM GENERATION
    Groq llama-3.3-70b receives:
      • System prompt (structured output format)
      • All k chunks as "# File: path (lines X-Y)\n<code>"
      • The question
    Returns: Summary → How it works → Key files → Code example → Caveats
   │
   ▼
Response with grounded answer + sources + pipeline label
("semantic" | "hybrid" | "hybrid+rerank" | "semantic+rerank")
```

---

## Chunking Strategy

Code is not prose — splitting it naively by character count destroys its semantic structure. We use **three strategies** depending on file type:

### 1. AST Chunking — Python files

Python files are parsed with the built-in `ast` module. Each **function definition** and **class definition** becomes exactly one chunk.

```python
# This entire function becomes one chunk, regardless of length
def calculate_order_total(items: list[Item], discount: float) -> Decimal:
    subtotal = sum(item.price * item.quantity for item in items)
    tax = subtotal * TAX_RATE
    return (subtotal + tax) * (1 - discount)
```

**Why:** An LLM needs the whole function to understand it. Cutting mid-function creates half-chunks that match no meaningful query. AST parse failures silently fall back to sliding window.

**Stored metadata:** `file_path`, `language`, `chunk_type` (function/class), `name`, `start_line`, `end_line`

---

### 2. Sliding Window Chunking — TypeScript, Go, Rust, YAML, etc.

Files without a Python-compatible AST parser use overlapping windows (default: 40 lines, 10 lines overlap).

```
Lines  1–40  → chunk A
Lines 31–70  → chunk B   ← 10 lines of overlap
Lines 61–100 → chunk C
```

**Why the overlap:** A function call on line 40 and its definition on line 41 would be in different chunks with zero shared context — the overlap prevents this. 10 lines is enough to preserve any meaningful cross-boundary context without excessive duplication.

---

### 3. Heading-based Chunking — Markdown

Markdown files split at `#`, `##`, `###` boundaries. Each section = one chunk. This keeps documentation coherent — a `## Configuration` section stays together.

---

### Trade-offs

| Strategy | Works for | Pro | Con |
|---|---|---|---|
| AST | Python only | Exact function boundaries | Requires valid Python AST |
| Sliding window | Any text file | Language-agnostic | May cut mid-function |
| Heading-based | Markdown | Preserves doc sections | Only for `.md` files |

**Files skipped automatically:** binaries, files > `MAX_FILE_SIZE_KB` (500 KB), lock files, build directories.

---

## Engineering Decisions

### ChromaDB over Qdrant / Pinecone / Weaviate

ChromaDB runs **embedded** — no separate Docker service, no network hop, no API key. For a project that runs on one container, this is strictly simpler. The HNSW index gives sub-millisecond search at tens of thousands of vectors.

Qdrant would be the right choice for multi-node horizontal scaling or production SLA requirements. Pinecone/Weaviate are managed services that require credit cards.

### Groq over OpenAI / Anthropic for inference

Groq's LPU hardware delivers ~200 tokens/second on llama-3.3-70b — ~10× faster than GPT-4o at the same context length. For a RAG service where answer latency is directly bottlenecked by inference speed, this matters. Free tier: 100 RPM / 6000 TPM. No credit card.

### `text-embedding-3-small` over `ada-002`

Same API, ~5× cheaper, comparable quality on code retrieval benchmarks. 1536 dimensions is sufficient for our corpus sizes.

### BM25 + RRF over pure semantic search

Semantic search handles conceptual questions ("how does authentication work?") but fails on exact lookups ("where is `JWT_SECRET` defined?"). BM25 excels at exact term matches. RRF combines both without a tunable weight parameter — a parameter-free formula from the IR literature (Cormack & Clarke, 2009).

The `RETRIEVAL_MULTIPLIER = 4` pattern: ChromaDB returns `k*4` candidates → reranker narrows to `k`. The wide net ensures the best chunks aren't excluded before the high-quality cross-encoder sees them.

### Cohere reranking as an optional layer

The reranker is a **cross-encoder**: it scores (question, chunk) pairs jointly rather than independently. This gives dramatically better relevance scores than cosine similarity (a bi-encoder approximation). Made optional because:
1. Adds API cost per query
2. Pipeline gracefully falls back to hybrid-only when key is absent
3. For small repos, quality difference is negligible

### structlog over Python `logging`

structlog outputs **JSON in production** and **colorized human-readable output in development** (controlled by `DEBUG` env var). Every log line is a structured event — no regex parsing needed to query logs in Datadog/Loki/CloudWatch.

### Single-worker Uvicorn

ChromaDB's `PersistentClient` is not safe across multiple processes. We run `--workers 1`. Horizontal scaling would require migrating to a standalone vector DB (Qdrant, etc.) — this is documented as a known limitation.

---

## Why NOT LangChain

LangChain wraps every AI primitive (embedders, vector stores, LLMs, retrievers) in abstract classes. We chose not to use it.

### 1. Abstraction cost > benefit at this scale

A LangChain chain for this pipeline is 6+ layers deep:  
`VectorStoreRetriever` → `RunnablePassthrough` → `ChatPromptTemplate` → `ChatGroq` → ...

When something breaks — wrong chunk format, empty retrieval, bad prompt — you debug through 4 inherited abstract classes to find the real error.

Our pipeline is 6 explicit functions you can step through in any debugger:  
`embed_query()` → `similarity_search()` → `bm25_search()` → `reciprocal_rank_fusion()` → `rerank()` → `generate_answer()`  
Every input/output is a typed Python dict. The implementation fits in one screen.

### 2. LangChain doesn't own the algorithms

BM25 + RRF is a known-optimal fusion algorithm from the information retrieval literature. LangChain's `EnsembleRetriever` does the same thing — but now the code is hidden behind a config dict and 3 levels of inheritance. Writing it yourself takes 50 lines and you understand every decision.

### 3. Version instability

LangChain ships breaking changes almost every minor version. A project built on LangChain 0.1 requires significant rework to run on 0.3. Our codebase has zero LangChain dependency — it runs on Python 3.13 today and will in three years.

### 4. This codebase IS the RAG library

After building this, the codebase is a reusable RAG toolkit:
- `hybrid_search.py` — drop-in BM25 + RRF for any search system
- `chunker.py` — AST + sliding window + markdown chunking
- `reranker.py` — Cohere reranking wrapper with graceful fallback
- `vector_store.py` — ChromaDB abstraction with collection management

> **The rule of thumb:** Use a framework when it saves you from writing code you don't understand. When you understand the algorithm, write it yourself and own it.

---

## Resilience & Fallbacks

| Failure scenario | Behavior |
|---|---|
| No `COHERE_API_KEY` | Reranker skipped, `pipeline = "hybrid"` |
| Cohere API error | Graceful fallback, warning logged, continues without rerank |
| GitHub rate limit (60 req/h) | HTTP 429 → `GITHUB_RATE_LIMITED` error. Set `GITHUB_TOKEN` env var for 5000/h |
| Repo not found | HTTP 404 → `REPO_NOT_FOUND` structured error |
| Repo not indexed | HTTP 404 → `REPO_NOT_INDEXED` with hint to run `/ingest` |
| Empty retrieval | Returns `"No relevant code found"` without calling LLM (saves tokens) |
| File too large | Skipped, logged as warning, rest of repo still indexed |
| Python AST parse failure | Automatic fallback to sliding window |
| Groq timeout | 500 response propagated to client |

All external HTTP calls use `httpx.AsyncClient` with `follow_redirects=True` (GitHub returns 301 redirects). Rate-limit retry logic lives in `app/utils/retry.py`.

---

## Limitations

- **Public repos only** — GitHub unauthenticated API: 60 req/hour. Set `GITHUB_TOKEN` for 5000/hour.
- **Ephemeral storage on HuggingFace Spaces** — ChromaDB resets on every Space redeploy. Re-index after deployments.
- **Python AST only** — TypeScript, Go, Rust, YAML use sliding window (good, not perfect).
- **No streaming responses** — answers are returned in one HTTP response. SSE streaming can be added to `llm.py` with minor changes.
- **Single-node ChromaDB** — not horizontally scalable. Migrate to Qdrant for multi-instance deployments.
- **Context window** — `k=5` with `RETRIEVAL_MULTIPLIER=4` = max 20 chunks of 40 lines ≈ ~8000 tokens of code context, well within Groq's 128K limit.
- **In-memory metrics** — `total_queries` and `avg_latency_ms` reset on restart. No persistence.

---

## Deployment

### HuggingFace Spaces (API — free, no credit card)

1. Create a Space at https://huggingface.co/new-space → choose **Docker** SDK
2. Push this repo (rename `HF_SPACES_README.md` to `README.md`, keeping the YAML frontmatter)
3. Add secrets in **Settings → Repository secrets**:

   | Secret | Value |
   |---|---|
   | `ANIMUSAI_API_KEY` | Your OpenAI-compatible key |
   | `ANIMUSAI_BASE_URL` | `https://api.openai.com/v1` |
   | `GROQ_API_KEY` | Your Groq key |
   | `COHERE_API_KEY` | Your Cohere key (optional) |

4. HuggingFace injects `PORT=7860` automatically — the Dockerfile handles it with `${PORT:-7860}`

**Health check:** `https://YOUR_SPACE.hf.space/health`

---

### Streamlit Cloud (Frontend — free, no credit card)

1. Push `streamlit_app.py` and `requirements_streamlit.txt` to your repo
2. Go to https://share.streamlit.io → **New app**
3. Set **Main file path** to `streamlit_app.py`
4. No secrets needed — the frontend only calls your HuggingFace API URL
5. In the app sidebar, enter your HuggingFace Space URL as the API base URL

---

### Local Docker Compose

```bash
docker compose up --build                    # API at localhost:8000
docker compose -f docker-compose.dev.yml up  # with hot-reload
```

---

## Development

```bash
# Install all deps
pip install -r requirements.txt -r requirements-dev.txt

# Lint (CI enforced)
ruff check app/
black --check app/

# Full test suite with coverage
pytest tests/ -v --cov=app --cov-report=term-missing

# CI requires ≥70% coverage
pytest tests/ --cov=app --cov-fail-under=70
```

### Test suite structure

| File | What it tests | Type |
|---|---|---|
| `test_health.py` | `GET /health` endpoint | Integration |
| `test_chunker.py` | AST + sliding window + markdown chunking | Unit |
| `test_github.py` | GitHub API client (mocked httpx) | Unit |
| `test_ingest.py` | `POST /ingest` full pipeline (9 tests) | Integration |
| `test_query.py` | `POST /query` full pipeline (7 tests) | Integration |
| `test_hybrid_search.py` | BM25 + RRF algorithms (14 tests) | Unit |

All integration tests mock every external call (no real network, no ChromaDB, no LLM). Uses `with patch()` context managers throughout — no `@patch` decorator ordering issues.

---

## Project Structure

```
gitrag/
├── app/
│   ├── main.py                # FastAPI app, structlog setup, lifespan
│   ├── config.py              # pydantic-settings v2 (all env vars)
│   ├── models/
│   │   └── schemas.py         # Pydantic request/response models
│   ├── routes/
│   │   ├── health.py          # GET /health + in-memory metrics
│   │   ├── ingest.py          # POST /ingest, DELETE /ingest/{url}
│   │   └── query.py           # POST /query (full RAG pipeline)
│   ├── services/
│   │   ├── github.py          # GitHub API client (httpx)
│   │   ├── chunker.py         # AST + sliding window + markdown chunking
│   │   ├── embedder.py        # OpenAI-compatible embeddings
│   │   ├── vector_store.py    # ChromaDB wrapper
│   │   ├── llm.py             # Groq LLM wrapper + structured prompt
│   │   ├── hybrid_search.py   # BM25 + RRF fusion
│   │   └── reranker.py        # Cohere reranking (optional)
│   ├── middleware/            # Reserved for auth / rate limiting
│   └── utils/
│       ├── hashing.py         # URL → stable repo_id
│       └── retry.py           # Exponential backoff decorator
├── tests/                     # pytest test suite (40 tests)
├── prompts/                   # Prompt templates + decision docs
├── streamlit_app.py           # Streamlit frontend (Streamlit Cloud)
├── Dockerfile                 # Python 3.13-slim, PORT env var support
├── docker-compose.yml         # Production single-node
├── docker-compose.dev.yml     # Development with hot-reload
├── requirements.txt           # API dependencies
├── requirements_streamlit.txt # Frontend dependencies (Streamlit Cloud)
├── requirements-dev.txt       # Dev/test dependencies
├── HF_SPACES_README.md        # HuggingFace Spaces README (rename on deploy)
└── .env.example               # Template — .env is gitignored
```

---

## License

MIT
