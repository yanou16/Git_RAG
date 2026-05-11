import time
import structlog
from groq import AsyncGroq
from app.config import get_settings
from app.utils.retry import with_retry

log = structlog.get_logger()
settings = get_settings()

SYSTEM_PROMPT = """You are a precise code analysis assistant.

Your role: answer questions about a specific GitHub repository using ONLY the provided code chunks.

Rules:
1. Answer based STRICTLY on the provided code chunks — never hallucinate
2. Always cite the specific file and approximate line number when referencing code
3. If the answer is not in the provided chunks, say: "I couldn't find relevant code for this in the indexed files."
4. Format code examples with proper markdown code blocks
5. Be concise but complete — developers need accurate answers, not long prose
6. If multiple files are relevant, mention all of them"""

RAG_PROMPT_TEMPLATE = """Here are the most relevant code chunks from the repository (ordered by relevance):

{chunks_formatted}

---

Question: {question}

Answer based only on the code above. Cite file paths and line numbers when relevant."""


class LLMService:
    def __init__(self):
        self.client = AsyncGroq(api_key=settings.GROQ_API_KEY)

    @with_retry(max_retries=3)
    async def generate_answer(
        self,
        question: str,
        chunks: list[dict],
        temperature: float = None
    ) -> tuple[str, int]:
        temperature = temperature or settings.GROQ_TEMPERATURE

        chunks_formatted = self._format_chunks(chunks)
        user_message = RAG_PROMPT_TEMPLATE.format(
            chunks_formatted=chunks_formatted,
            question=question
        )

        start = time.time()
        response = await self.client.chat.completions.create(
            model=settings.GROQ_MODEL,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_message}
            ],
            max_tokens=settings.GROQ_MAX_TOKENS,
            temperature=temperature
        )

        latency_ms = round((time.time() - start) * 1000, 2)
        tokens_used = response.usage.total_tokens
        answer = response.choices[0].message.content

        log.info("llm_call",
                 model=settings.GROQ_MODEL,
                 tokens_used=tokens_used,
                 latency_ms=latency_ms,
                 chunks_count=len(chunks))

        return answer, tokens_used

    def _format_chunks(self, chunks: list[dict]) -> str:
        formatted = []
        for i, chunk in enumerate(chunks, 1):
            meta = chunk["metadata"]
            score = round(chunk["score"], 3)
            formatted.append(
                f"[Chunk {i}] {meta['file_path']} "
                f"(lines {meta.get('start_line', '?')}-{meta.get('end_line', '?')}) "
                f"[similarity: {score}]\n"
                f"```{meta.get('language', '')}\n"
                f"{chunk['text'][:1500]}\n"
                f"```"
            )
        return "\n\n".join(formatted)
