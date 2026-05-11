import structlog
import cohere
from app.config import get_settings
from app.utils.retry import with_retry

log = structlog.get_logger()
settings = get_settings()


class RerankerService:
    """
    Cohere Rerank v3.5 — takes top-N semantic results and re-scores
    them against the actual query. Consistently adds 15-25% precision.

    Why reranking works:
      Embedding similarity = "these texts look alike"
      Reranking           = "this chunk actually ANSWERS the question"
    Those are different things. A chunk about error handling in login()
    may be semantically close to "how does auth work?" but not the best
    answer. Reranker catches that.
    """

    def __init__(self):
        if not settings.COHERE_API_KEY:
            self.client = None
            return
        self.client = cohere.AsyncClientV2(api_key=settings.COHERE_API_KEY)
        self.model = "rerank-v3.5"

    @property
    def available(self) -> bool:
        return self.client is not None

    @with_retry(max_retries=2)
    async def rerank(
        self,
        query: str,
        chunks: list[dict],
        top_n: int = 5,
    ) -> list[dict]:
        """
        Rerank chunks by relevance to the query.
        Returns top_n chunks in new order with rerank_score added.
        Falls back gracefully if Cohere is unavailable.
        """
        if not self.available or not chunks:
            return chunks[:top_n]

        # Cohere expects plain strings, we trim to 512 chars for speed
        documents = [c["text"][:512] for c in chunks]

        response = await self.client.rerank(
            model=self.model,
            query=query,
            documents=documents,
            top_n=min(top_n, len(chunks)),
        )

        reranked = []
        for result in response.results:
            chunk = dict(chunks[result.index])
            chunk["rerank_score"] = round(result.relevance_score, 4)
            # Replace semantic score with rerank score for downstream display
            chunk["score"] = round(result.relevance_score, 4)
            reranked.append(chunk)

        log.info(
            "rerank_done",
            model=self.model,
            input_chunks=len(chunks),
            output_chunks=len(reranked),
            top_score=reranked[0]["rerank_score"] if reranked else 0,
        )
        return reranked
