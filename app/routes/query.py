import time
import structlog
from fastapi import APIRouter, HTTPException
from app.config import get_settings
from app.models.schemas import QueryRequest, QueryResponse, Source
from app.services.embedder import EmbedderService
from app.services.vector_store import VectorStore
from app.services.llm import LLMService
from app.services.reranker import RerankerService
from app.services.hybrid_search import bm25_search, reciprocal_rank_fusion
from app.utils.hashing import url_to_repo_id
from app.routes.health import _metrics

settings = get_settings()

router = APIRouter()
log = structlog.get_logger()

# How many candidates we fetch before reranking.
# We cast a wide net (k * 4) then let the reranker pick the best k.
RETRIEVAL_MULTIPLIER = 4


@router.post("/query", response_model=QueryResponse)
async def query_repo(request: QueryRequest):
    start_time = time.time()
    repo_id = url_to_repo_id(request.repo_url)

    embedder = EmbedderService()
    vector_store = VectorStore()
    llm = LLMService()
    reranker = RerankerService()

    if not vector_store.collection_exists(repo_id):
        raise HTTPException(
            status_code=404,
            detail={
                "error": "Repository not indexed",
                "detail": f"Run POST /ingest first for {request.repo_url}",
                "code": "REPO_NOT_INDEXED",
            },
        )

    # ── Step 1: embed the question ─────────────────────────────────────────
    query_embedding = await embedder.embed_query(request.question)

    # ── Step 2: semantic search — cast a wide net ──────────────────────────
    # We fetch k*4 candidates so the reranker has more to work with.
    candidate_k = request.k * RETRIEVAL_MULTIPLIER
    semantic_chunks = vector_store.similarity_search(
        repo_id,
        query_embedding,
        k=candidate_k,
        language_filter=request.language,
    )

    if not semantic_chunks:
        return QueryResponse(
            answer="No relevant code found for this question in the indexed repository.",
            sources=[],
            repo_id=repo_id,
            repo_url=request.repo_url,
            question=request.question,
            latency_ms=round((time.time() - start_time) * 1000, 2),
            tokens_used=0,
            model="none",
            k_retrieved=0,
            pipeline="semantic",
        )

    # ── Step 3: hybrid search (BM25 + semantic via RRF) ───────────────────
    pipeline = "semantic"
    if request.use_hybrid:
        bm25_chunks = bm25_search(request.question, semantic_chunks, top_n=candidate_k)
        chunks = reciprocal_rank_fusion(semantic_chunks, bm25_chunks)
        pipeline = "hybrid"
    else:
        chunks = semantic_chunks

    # ── Step 4: Cohere reranking ───────────────────────────────────────────
    # We rerank the hybrid candidates down to the final k.
    if request.use_reranking and reranker.available:
        chunks = await reranker.rerank(request.question, chunks, top_n=request.k)
        pipeline = "hybrid+rerank" if "hybrid" in pipeline else "semantic+rerank"
    else:
        chunks = chunks[: request.k]

    # ── Step 5: generate answer with upgraded prompt ───────────────────────
    answer, tokens_used = await llm.generate_answer(
        question=request.question,
        chunks=chunks,
        temperature=request.temperature,
        repo_url=request.repo_url,
    )

    # ── Step 6: build sources ──────────────────────────────────────────────
    sources = [
        Source(
            file_path=c["metadata"]["file_path"],
            start_line=c["metadata"].get("start_line"),
            end_line=c["metadata"].get("end_line"),
            language=c["metadata"].get("language", "unknown"),
            similarity_score=round(c["score"], 4),
            rerank_score=c.get("rerank_score"),
            excerpt=c["text"][:200],
        )
        for c in chunks
    ]

    latency_ms = round((time.time() - start_time) * 1000, 2)
    _metrics["total_queries"] += 1
    _metrics["total_latency_ms"] += latency_ms

    log.info(
        "query_completed",
        repo_id=repo_id,
        pipeline=pipeline,
        candidates_fetched=len(semantic_chunks),
        chunks_to_llm=len(chunks),
        tokens_used=tokens_used,
        latency_ms=latency_ms,
        reranking_used=reranker.available and request.use_reranking,
    )

    return QueryResponse(
        answer=answer,
        sources=sources,
        repo_id=repo_id,
        repo_url=request.repo_url,
        question=request.question,
        latency_ms=latency_ms,
        tokens_used=tokens_used,
        model=settings.GROQ_MODEL,
        k_retrieved=len(chunks),
        pipeline=pipeline,
    )

