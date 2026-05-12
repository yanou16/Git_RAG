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

# GitRAG — GitHub Codebase Q&A API

A production-grade RAG API that lets you ask natural-language questions about any public GitHub repository.

## Deployment

This Space runs the **FastAPI backend** via Docker.

### Required Secrets (set in Space Settings → Secrets)

| Secret | Description |
|--------|-------------|
| `ANIMUSAI_API_KEY` | OpenAI-compatible key for embeddings (text-embedding-3-small) |
| `ANIMUSAI_BASE_URL` | Base URL, e.g. `https://api.openai.com/v1` |
| `GROQ_API_KEY` | Groq API key for LLM inference (llama-3.3-70b) |
| `COHERE_API_KEY` | *(Optional)* Cohere key for reranking — pipeline degrades gracefully without it |

### Health check

```
GET https://<your-space>.hf.space/health
```

### Quick test

```bash
# Index a repo
curl -X POST https://<your-space>.hf.space/ingest \
  -H "Content-Type: application/json" \
  -d '{"repo_url": "https://github.com/tiangolo/fastapi"}'

# Ask a question
curl -X POST https://<your-space>.hf.space/query \
  -H "Content-Type: application/json" \
  -d '{"repo_url": "https://github.com/tiangolo/fastapi", "question": "How does dependency injection work?"}'
```

## Notes

- ChromaDB data is stored at `/app/chroma_data` — **ephemeral on HuggingFace** (resets on redeploy). Re-index after each redeploy.
- PORT is injected automatically by HuggingFace as `7860`.
- The Dockerfile uses `CMD ["sh", "-c", "uvicorn ... --port ${PORT:-7860}"]` to respect this.
