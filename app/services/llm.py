import time
import structlog
from groq import AsyncGroq
from app.config import get_settings
from app.utils.retry import with_retry

log = structlog.get_logger()
settings = get_settings()

# ── Level-2 system prompt ────────────────────────────────────────────────────
# Improvement over v1:
#   - Asks for structured flow (entry → logic → output) not just raw facts
#   - Asks to surface potential bugs spotted in the relevant code
#   - Explicitly tells it to link files when they call each other
#   - Strict "say so" rule prevents confident hallucinations
SYSTEM_PROMPT = """You are an expert software engineer answering questions about a GitHub repository.
You have been given ranked code chunks retrieved from the codebase. Use them to answer accurately.

## Rules (non-negotiable):
1. Answer in the SAME LANGUAGE as the question (French question → French answer, English → English, etc.)
2. Use ONLY information from the provided chunks — never hallucinate
3. If the answer is not in the chunks, say exactly: "The answer is not in the indexed files for this repo."
4. Always cite `file_path` lines X-Y when you reference code
5. Never invent function names, signatures, or behavior

## Format — adapt to the question type:

**Simple/factual question** (yes/no, what is X, does it have Y):
→ Answer directly in 2-4 sentences, cite relevant files, done.

**How does X work / explain X**:
→ **Answer** — direct one-line response
→ **Flow** — entry point → core logic → output (bullet points)
→ **Key files** — `path` lines X-Y — role in the answer
→ **Code** (only if a snippet genuinely helps, taken verbatim from chunks)

**Debugging / what's wrong / edge cases**:
→ Answer + point to the exact lines + explain the risk

Never pad the response with empty sections. If "Code example" adds nothing, skip it."""

RAG_PROMPT_TEMPLATE = """## Code chunks retrieved (ranked by relevance to your question):

{chunks_formatted}

---

## Developer question:
{question}

Answer using the structure from your instructions. Every claim must be backed by a specific chunk above."""


class LLMService:
    def __init__(self):
        self.client = AsyncGroq(api_key=settings.GROQ_API_KEY)

    @with_retry(max_retries=3)
    async def generate_answer(
        self,
        question: str,
        chunks: list[dict],
        temperature: float = None,
        repo_url: str = "",
    ) -> tuple[str, int]:
        temperature = temperature or settings.GROQ_TEMPERATURE

        chunks_formatted = self._format_chunks(chunks)
        user_message = RAG_PROMPT_TEMPLATE.format(
            chunks_formatted=chunks_formatted,
            question=question,
        )

        start = time.time()
        response = await self.client.chat.completions.create(
            model=settings.GROQ_MODEL,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_message},
            ],
            max_tokens=settings.GROQ_MAX_TOKENS,
            temperature=temperature,
        )

        latency_ms = round((time.time() - start) * 1000, 2)
        tokens_used = response.usage.total_tokens
        answer = response.choices[0].message.content

        log.info(
            "llm_call",
            model=settings.GROQ_MODEL,
            tokens_used=tokens_used,
            latency_ms=latency_ms,
            chunks_count=len(chunks),
        )

        return answer, tokens_used

    def _format_chunks(self, chunks: list[dict]) -> str:
        """
        Format chunks for the prompt. Shows rerank score when available,
        otherwise semantic score. Includes BM25 signal as a label.
        """
        formatted = []
        for i, chunk in enumerate(chunks, 1):
            meta = chunk["metadata"]

            # Show the best available score
            if "rerank_score" in chunk:
                score_label = f"rerank={chunk['rerank_score']}"
            elif "rrf_score" in chunk:
                score_label = f"hybrid_rrf={chunk['rrf_score']}"
            else:
                score_label = f"semantic={round(chunk['score'], 3)}"

            formatted.append(
                f"### Chunk {i} — `{meta['file_path']}` "
                f"lines {meta.get('start_line', '?')}-{meta.get('end_line', '?')} "
                f"[{score_label}]\n"
                f"```{meta.get('language', '')}\n"
                f"{chunk['text'][:1500]}\n"
                f"```"
            )
        return "\n\n".join(formatted)
