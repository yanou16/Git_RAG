# GitRAG — GitHub Codebase Q&A API

[![CI](https://github.com/yanou16/gitrag/actions/workflows/ci.yml/badge.svg)](https://github.com/yanou16/gitrag/actions/workflows/ci.yml)

API RAG production-grade : posez des questions en langage naturel sur n'importe quel repo GitHub public. Répond avec les sources citées (fichier + ligne).

## Architecture

```
GitHub Repo
    │
    ▼
POST /ingest ──► GitHub API ──► Chunker (AST/sliding) ──► AnimusAI Embeddings ──► ChromaDB
                                                                                        │
POST /query  ──► AnimusAI Embeddings ──► ChromaDB similarity search ──────────────────►│
                                                    │                                   │
                                                    ▼
                                            Groq (llama-3.3-70b)
                                                    │
                                                    ▼
                                           Answer + Sources
```

## Quick Start

```bash
# 1. Clone
git clone https://github.com/yanou16/gitrag
cd gitrag

# 2. Configure
cp .env.example .env
# Remplir ANIMUSAI_API_KEY et GROQ_API_KEY dans .env

# 3. Run
docker-compose up --build

# 4. Vérifier
curl http://localhost:8000/health
```

## API Reference

### POST /ingest
Indexer un repo GitHub.

```bash
curl -X POST http://localhost:8000/ingest \
  -H "Content-Type: application/json" \
  -d '{
    "repo_url": "https://github.com/tiangolo/fastapi",
    "branch": "master",
    "max_files": 100
  }'
```

Response:
```json
{
  "repo_id": "a3f1b2c4d5e6",
  "repo_url": "https://github.com/tiangolo/fastapi",
  "files_indexed": 87,
  "chunks_stored": 412,
  "duration_ms": 18432.5,
  "was_cached": false,
  "warnings": []
}
```

### POST /query
Poser une question sur un repo indexé.

```bash
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{
    "repo_url": "https://github.com/tiangolo/fastapi",
    "question": "How does dependency injection work?",
    "k": 5
  }'
```

Response:
```json
{
  "answer": "FastAPI uses a `Depends` decorator...",
  "sources": [
    {
      "file_path": "fastapi/dependencies/utils.py",
      "start_line": 42,
      "end_line": 87,
      "language": "python",
      "similarity_score": 0.923,
      "excerpt": "# File: fastapi/dependencies/utils.py\nasync def solve_dependencies..."
    }
  ],
  "latency_ms": 1243.7,
  "tokens_used": 512,
  "model": "llama-3.3-70b-versatile",
  "k_retrieved": 5
}
```

### GET /health
```bash
curl http://localhost:8000/health
```

### GET /metrics
```bash
curl http://localhost:8000/metrics
```

### DELETE /repos/{repo_id}
Supprimer l'index d'un repo.

```bash
curl -X DELETE http://localhost:8000/repos/a3f1b2c4d5e6
```

## Resilience

### Rate Limits

| Service | Limit | Strategy |
|---|---|---|
| GitHub API (no token) | 60 req/h | Retry + backoff. Set `GITHUB_TOKEN` for 5000 req/h |
| GitHub API (with token) | 5000 req/h | Sufficient for most repos |
| AnimusAI Embeddings | Varies | Batch 100 texts/call. Retry 3× with exponential backoff |
| Groq LLM | ~30 RPM free | Retry 3× with backoff. Returns 429 after exhaustion |

### Timeouts

| Service | Timeout | Reason |
|---|---|---|
| GitHub API | 10s | GitHub p99 latency < 5s |
| AnimusAI embeddings | 20s | Batch embedding can take 15s |
| Groq LLM | 30s | Large context window calls |

### Fallbacks

- Repo > `max_files` → index first N files + warning in response
- File > 100 KB → skip + log
- Python AST parse failure → fallback to sliding window
- Chunk < 50 chars → silently skipped
- Groq rate limit after 3 retries → HTTP 429
- ChromaDB unavailable → HTTP 503

## Limitations

- Repos privés non supportés (nécessite token utilisateur — v2)
- Repos > 500 fichiers : ingestion lente (2–5 min), qualité dégradée
- Pas d'AST pour TypeScript/Go/Rust (sliding window uniquement)
- Pas de queries cross-repo
- ChromaDB ephémère sur Render free tier (reset au redeploy)
- Métriques en mémoire (reset au restart) — pas de persistance Redis

## Engineering Decisions

Voir [`prompts/engineering_decisions.md`](prompts/engineering_decisions.md) pour le détail complet.

- **ChromaDB** vs Qdrant : zéro dépendance externe, client Python natif, parfait pour Render free tier
- **Groq** vs OpenAI : latence ~10× inférieure, free tier généreux, llama-3.3-70b fort sur le code
- **AnimusAI** vs OpenAI embeddings : API-compatible OpenAI, free tier pour le dev
- **FastAPI** : async natif, OpenAPI auto, Pydantic validation
- **Single-worker Uvicorn** : ChromaDB PersistentClient non thread-safe multi-process

## Live URL

🔗 [https://gitrag.onrender.com](https://gitrag.onrender.com) *(à compléter après deploy)*
