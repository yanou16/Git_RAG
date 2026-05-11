import httpx
import base64
import structlog
from app.config import get_settings
from app.utils.retry import with_retry

log = structlog.get_logger()
settings = get_settings()

SUPPORTED_EXTENSIONS = {
    ".py": "python",
    ".ts": "typescript",
    ".tsx": "typescript",
    ".js": "javascript",
    ".jsx": "javascript",
    ".go": "go",
    ".rs": "rust",
    ".md": "markdown",
    ".yaml": "yaml",
    ".yml": "yaml",
}


class GitHubService:
    def __init__(self):
        headers = {"Accept": "application/vnd.github.v3+json"}
        if settings.GITHUB_TOKEN:
            headers["Authorization"] = f"token {settings.GITHUB_TOKEN}"
        self.client = httpx.AsyncClient(
            base_url=settings.GITHUB_API_BASE,
            headers=headers,
            timeout=httpx.Timeout(settings.GITHUB_TIMEOUT_SECONDS)
        )

    @with_retry(max_retries=3)
    async def list_files(
        self,
        owner: str,
        repo: str,
        branch: str = "main",
        extensions: list[str] = None
    ) -> list[dict]:
        extensions = extensions or list(SUPPORTED_EXTENSIONS.keys())

        response = await self.client.get(
            f"/repos/{owner}/{repo}/git/trees/{branch}?recursive=1"
        )

        if response.status_code == 404:
            raise RepoNotFoundError(f"Repo {owner}/{repo} not found or is private")
        if response.status_code == 409:
            raise RepoEmptyError(f"Repo {owner}/{repo} is empty")

        response.raise_for_status()
        tree = response.json()

        files = []
        for item in tree.get("tree", []):
            if item["type"] != "blob":
                continue
            path = item["path"]
            ext = "." + path.rsplit(".", 1)[-1] if "." in path else ""
            if ext not in extensions:
                continue
            files.append({
                "path": path,
                "size": item.get("size", 0),
                "sha": item["sha"],
                "language": SUPPORTED_EXTENSIONS.get(ext, "other")
            })

        log.info("github_files_listed", owner=owner, repo=repo, total_files=len(files))
        return files

    @with_retry(max_retries=3)
    async def get_file_content(self, owner: str, repo: str, path: str) -> str | None:
        response = await self.client.get(
            f"/repos/{owner}/{repo}/contents/{path}"
        )
        if response.status_code == 404:
            return None
        response.raise_for_status()

        data = response.json()
        if data.get("encoding") == "base64":
            return base64.b64decode(data["content"]).decode("utf-8", errors="replace")
        return data.get("content", "")

    async def close(self):
        await self.client.aclose()


class RepoNotFoundError(Exception):
    pass


class RepoEmptyError(Exception):
    pass
