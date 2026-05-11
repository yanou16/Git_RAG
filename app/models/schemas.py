from pydantic import BaseModel, Field, field_validator
from typing import Optional
from enum import Enum


class Language(str, Enum):
    PYTHON = "python"
    TYPESCRIPT = "typescript"
    JAVASCRIPT = "javascript"
    GO = "go"
    RUST = "rust"
    MARKDOWN = "markdown"
    YAML = "yaml"
    OTHER = "other"


# ─── INGEST ────────────────────────────────────────────────

class IngestRequest(BaseModel):
    repo_url: str = Field(
        ...,
        description="GitHub repo URL public",
        examples=["https://github.com/tiangolo/fastapi"]
    )
    branch: str = Field(default="main", description="Branch à indexer")
    file_extensions: list[str] = Field(
        default=[".py", ".ts", ".js", ".tsx", ".go", ".rs", ".md", ".yaml"],
        description="Extensions de fichiers à indexer"
    )
    max_files: int = Field(default=200, ge=1, le=500)
    force_reindex: bool = Field(
        default=False,
        description="Forcer la ré-indexation même si déjà fait"
    )

    @field_validator("repo_url")
    @classmethod
    def validate_github_url(cls, v: str) -> str:
        if "github.com" not in v:
            raise ValueError("URL doit être un repo GitHub")
        return v.rstrip("/")


class IngestResponse(BaseModel):
    repo_id: str
    repo_url: str
    files_indexed: int
    chunks_stored: int
    duration_ms: float
    was_cached: bool = False
    warnings: list[str] = []


# ─── QUERY ─────────────────────────────────────────────────

class QueryRequest(BaseModel):
    repo_url: str
    question: str = Field(..., min_length=3, max_length=500)
    k: int = Field(default=5, ge=1, le=20, description="Chunks à retriever")
    temperature: float = Field(default=0.1, ge=0.0, le=1.0)
    language: Optional[str] = Field(
        default=None,
        description="Filtrer sur un langage spécifique"
    )


class Source(BaseModel):
    file_path: str
    start_line: Optional[int]
    end_line: Optional[int]
    language: str
    similarity_score: float
    excerpt: str = Field(..., description="200 chars du chunk")


class QueryResponse(BaseModel):
    answer: str
    sources: list[Source]
    repo_id: str
    repo_url: str
    question: str
    latency_ms: float
    tokens_used: int
    model: str
    k_retrieved: int


# ─── HEALTH ────────────────────────────────────────────────

class HealthResponse(BaseModel):
    status: str  # "healthy" | "degraded" | "unhealthy"
    version: str
    uptime_seconds: float
    chroma_status: str
    groq_status: str


class MetricsResponse(BaseModel):
    indexed_repos: int
    total_chunks: int
    total_queries: int
    avg_query_latency_ms: float
    uptime_seconds: float
    errors_last_hour: int


# ─── ERRORS ────────────────────────────────────────────────

class ErrorResponse(BaseModel):
    error: str
    detail: str
    code: str  # "REPO_NOT_FOUND" | "RATE_LIMIT" | "REPO_TOO_LARGE" etc.
