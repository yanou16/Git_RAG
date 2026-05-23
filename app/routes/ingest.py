import time
import asyncio
import structlog
from fastapi import APIRouter, HTTPException
from app.models.schemas import IngestRequest, IngestResponse
from app.services.github import GitHubService, RepoNotFoundError
from app.services.chunker import chunk_file
from app.services.embedder import EmbedderService
from app.services.vector_store import VectorStore
from app.utils.hashing import url_to_repo_id
from app.config import get_settings

router = APIRouter()
log = structlog.get_logger()
settings = get_settings()


@router.post("/ingest", response_model=IngestResponse)
async def ingest_repo(request: IngestRequest):
    start_time = time.time()
    warnings = []

    parts = request.repo_url.rstrip("/").split("/")
    if len(parts) < 2:
        raise HTTPException(400, "URL GitHub invalide")
    owner, repo = parts[-2], parts[-1]

    repo_id = url_to_repo_id(request.repo_url)

    github = GitHubService()
    embedder = EmbedderService()
    vector_store = VectorStore()

    if vector_store.collection_exists(repo_id) and not request.force_reindex:
        log.info("ingest_cache_hit", repo_id=repo_id)
        return IngestResponse(
            repo_id=repo_id,
            repo_url=request.repo_url,
            files_indexed=0,
            chunks_stored=0,
            duration_ms=round((time.time() - start_time) * 1000, 2),
            was_cached=True,
        )

    try:
        files = await github.list_files(
            owner, repo, branch=request.branch, extensions=request.file_extensions
        )

        if len(files) > request.max_files:
            warnings.append(
                f"Repo has {len(files)} files. Only indexing first {request.max_files}."
            )
            files = files[: request.max_files]

        if not files:
            raise HTTPException(404, "No supported files found in repository")

        all_chunks = []
        semaphore = asyncio.Semaphore(10)

        async def process_file(file_info: dict) -> list:
            async with semaphore:
                if file_info.get("size", 0) > settings.GITHUB_MAX_FILE_SIZE_KB * 1024:
                    log.info(
                        "file_skipped_too_large",
                        path=file_info["path"],
                        size_kb=file_info["size"] // 1024,
                    )
                    return []

                content = await github.get_file_content(owner, repo, file_info["path"])
                if not content:
                    return []

                return chunk_file(content, file_info["path"], file_info["language"])

        tasks = [process_file(f) for f in files]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        for result in results:
            if isinstance(result, list):
                all_chunks.extend(result)
            elif isinstance(result, Exception):
                log.warning("file_processing_error", error=str(result))

        if not all_chunks:
            raise HTTPException(
                422, "No content could be extracted from repository files"
            )

        texts = [c.text for c in all_chunks]
        embeddings = await embedder.embed_texts(texts)

        stored = vector_store.upsert_chunks(repo_id, all_chunks, embeddings)

        duration_ms = round((time.time() - start_time) * 1000, 2)
        log.info(
            "ingest_completed",
            repo_id=repo_id,
            files_indexed=len(files),
            chunks_stored=stored,
            duration_ms=duration_ms,
        )

        return IngestResponse(
            repo_id=repo_id,
            repo_url=request.repo_url,
            files_indexed=len(files),
            chunks_stored=stored,
            duration_ms=duration_ms,
            was_cached=False,
            warnings=warnings,
        )

    except RepoNotFoundError as e:
        raise HTTPException(
            status_code=404,
            detail={
                "error": "Repo not found",
                "detail": str(e),
                "code": "REPO_NOT_FOUND",
            },
        )
    finally:
        await github.close()


@router.delete("/repos/{repo_id}")
async def delete_repo(repo_id: str):
    vector_store = VectorStore()
    if not vector_store.collection_exists(repo_id):
        raise HTTPException(404, f"Repo {repo_id} not indexed")
    vector_store.delete_collection(repo_id)
    log.info("repo_deleted", repo_id=repo_id)
    return {"message": f"Repo {repo_id} deleted", "repo_id": repo_id}
