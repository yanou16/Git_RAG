import asyncio
import functools
import structlog

log = structlog.get_logger()


def with_retry(max_retries: int = 3, exceptions=(Exception,)):
    """Exponential backoff retry decorator for async functions."""
    def decorator(func):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            # Import here to avoid circular import at module load time
            from app.config import get_settings
            settings = get_settings()

            for attempt in range(max_retries + 1):
                try:
                    return await func(*args, **kwargs)
                except exceptions as e:
                    if attempt == max_retries:
                        log.error("retry_exhausted",
                                  function=func.__name__,
                                  attempts=attempt + 1,
                                  error=str(e))
                        raise

                    delay = min(
                        settings.RETRY_BASE_DELAY_SECONDS * (2 ** attempt),
                        settings.RETRY_MAX_DELAY_SECONDS
                    )
                    log.warning("retry_attempt",
                                function=func.__name__,
                                attempt=attempt + 1,
                                delay_seconds=delay,
                                error=str(e))
                    await asyncio.sleep(delay)
        return wrapper
    return decorator
