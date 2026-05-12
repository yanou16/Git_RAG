FROM python:3.13-slim

WORKDIR /app

RUN apt-get update && \
    apt-get install -y --no-install-recommends git curl && \
    rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app/ ./app/
COPY prompts/ ./prompts/

# chroma_data is a volume for persistence
# On HuggingFace Spaces the filesystem is ephemeral — data resets on redeploy
RUN mkdir -p /app/chroma_data
VOLUME ["/app/chroma_data"]

# PORT defaults to 8000 locally.
# HuggingFace Spaces injects PORT=7860 automatically.
EXPOSE 7860

HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:${PORT:-7860}/health || exit 1

CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-7860} --workers 1 --log-level info"]
