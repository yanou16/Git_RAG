import hashlib


def url_to_repo_id(repo_url: str) -> str:
    """Convert a GitHub URL to a stable short repo_id (12-char hex)."""
    normalized = repo_url.rstrip("/").lower()
    return hashlib.sha256(normalized.encode()).hexdigest()[:12]
