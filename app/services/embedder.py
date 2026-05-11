import time
import structlog
from openai import AsyncOpenAI
from app.config import get_settings
from app.utils.retry import with_retry

log = structlog.get_logger()
settings = get_settings()


class EmbedderService:
    def __init__(self):
        self.client = AsyncOpenAI(
            base_url=settings.ANIMUSAI_BASE_URL,
            api_key=settings.ANIMUSAI_API_KEY,
        )
        self.model = settings.EMBEDDING_MODEL

    @with_retry(max_retries=3)
    async def embed_texts(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []

        all_embeddings = []
        batch_size = settings.EMBEDDING_BATCH_SIZE

        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            start = time.time()

            response = await self.client.embeddings.create(
                input=batch,
                model=self.model
            )

            embeddings = [item.embedding for item in response.data]
            all_embeddings.extend(embeddings)

            log.info("embed_batch",
                     model=self.model,
                     batch_size=len(batch),
                     latency_ms=round((time.time() - start) * 1000, 2))

        return all_embeddings

    @with_retry(max_retries=3)
    async def embed_query(self, text: str) -> list[float]:
        start = time.time()
        response = await self.client.embeddings.create(
            input=[text],
            model=self.model
        )
        log.info("embed_query",
                 model=self.model,
                 latency_ms=round((time.time() - start) * 1000, 2))
        return response.data[0].embedding
