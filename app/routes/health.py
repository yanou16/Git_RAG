import time
import structlog
from fastapi import APIRouter
from app.models.schemas import HealthResponse, MetricsResponse
from app.services.vector_store import VectorStore
from app.config import get_settings

router = APIRouter()
log = structlog.get_logger()
settings = get_settings()
START_TIME = time.time()

# In-memory counters (replace with Redis in a real multi-worker setup)
_metrics = {
    "total_queries": 0,
    "total_latency_ms": 0.0,
    "errors_last_hour": 0
}


@router.get("/health", response_model=HealthResponse)
async def health_check():
    vector_store = VectorStore()

    try:
        vector_store.get_stats()
        chroma_status = "ok"
    except Exception as e:
        chroma_status = f"error: {e}"

    groq_status = "ok" if settings.GROQ_API_KEY else "no_api_key"
    status = "healthy" if chroma_status == "ok" else "degraded"

    return HealthResponse(
        status=status,
        version=settings.VERSION,
        uptime_seconds=round(time.time() - START_TIME, 2),
        chroma_status=chroma_status,
        groq_status=groq_status
    )


@router.get("/metrics", response_model=MetricsResponse)
async def get_metrics():
    vector_store = VectorStore()
    stats = vector_store.get_stats()

    avg_latency = (
        _metrics["total_latency_ms"] / _metrics["total_queries"]
        if _metrics["total_queries"] > 0 else 0.0
    )

    return MetricsResponse(
        indexed_repos=stats["indexed_repos"],
        total_chunks=stats["total_chunks"],
        total_queries=_metrics["total_queries"],
        avg_query_latency_ms=round(avg_latency, 2),
        uptime_seconds=round(time.time() - START_TIME, 2),
        errors_last_hour=_metrics["errors_last_hour"]
    )
