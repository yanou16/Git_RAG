import time
import structlog
from fastapi import APIRouter, HTTPException
from app.models.schemas import QueryRequest, QueryResponse, Source
from app.services.embedder import EmbedderService
from app.services.vector_store import VectorStore
from app.services.llm import LLMService
from app.utils.hashing import url_to_repo_id
from app.routes.health import _metrics

router = APIRouter()
log = structlog.get_logger()


@router.post("/query", response_model=QueryResponse)
async def query_repo(request: QueryRequest):
    start_time = time.time()

    repo_id = url_to_repo_id(request.repo_url)

    embedder = EmbedderService()
    vector_store = VectorStore()
    llm = LLMService()

    if not vector_store.collection_exists(repo_id):
        raise HTTPException(
            status_code=404,
            detail={
                "error": "Repository not indexed",
                "detail": f"Run POST /ingest first for {request.repo_url}",
                "code": "REPO_NOT_INDEXED"
            }
        )

    query_embedding = await embedder.embed_query(request.question)

    chunks = vector_store.similarity_search(
        repo_id,
        query_embedding,
        k=request.k,
        language_filter=request.language
    )

    if not chunks:
        return QueryResponse(
            answer="No relevant code found for this question in the indexed repository.",
            sources=[],
            repo_id=repo_id,
            repo_url=request.repo_url,
            question=request.question,
            latency_ms=round((time.time() - start_time) * 1000, 2),
            tokens_used=0,
            model="none",
            k_retrieved=0
        )

    answer, tokens_used = await llm.generate_answer(
        question=request.question,
        chunks=chunks,
        temperature=request.temperature
    )

    sources = [
        Source(
            file_path=c["metadata"]["file_path"],
            start_line=c["metadata"].get("start_line"),
            end_line=c["metadata"].get("end_line"),
            language=c["metadata"].get("language", "unknown"),
            similarity_score=round(c["score"], 4),
            excerpt=c["text"][:200]
        )
        for c in chunks
    ]

    latency_ms = round((time.time() - start_time) * 1000, 2)

    _metrics["total_queries"] += 1
    _metrics["total_latency_ms"] += latency_ms

    log.info("query_completed",
             repo_id=repo_id,
             question_length=len(request.question),
             chunks_retrieved=len(chunks),
             tokens_used=tokens_used,
             latency_ms=latency_ms)

    return QueryResponse(
        answer=answer,
        sources=sources,
        repo_id=repo_id,
        repo_url=request.repo_url,
        question=request.question,
        latency_ms=latency_ms,
        tokens_used=tokens_used,
        model="llama-3.3-70b-versatile",
        k_retrieved=len(chunks)
    )
