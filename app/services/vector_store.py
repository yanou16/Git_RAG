import chromadb
from chromadb.config import Settings as ChromaSettings
import structlog
from app.config import get_settings
from app.services.chunker import Chunk

log = structlog.get_logger()
settings = get_settings()


class VectorStore:
    def __init__(self):
        self.client = chromadb.PersistentClient(
            path=settings.CHROMA_PERSIST_DIR,
            settings=ChromaSettings(anonymized_telemetry=False)
        )

    def _collection_name(self, repo_id: str) -> str:
        prefix = settings.CHROMA_COLLECTION_PREFIX
        return f"{prefix}{repo_id[:50]}"

    def collection_exists(self, repo_id: str) -> bool:
        try:
            self.client.get_collection(self._collection_name(repo_id))
            return True
        except Exception:
            return False

    def get_or_create_collection(self, repo_id: str):
        return self.client.get_or_create_collection(
            name=self._collection_name(repo_id),
            metadata={"hnsw:space": "cosine"}
        )

    def upsert_chunks(
        self,
        repo_id: str,
        chunks: list[Chunk],
        embeddings: list[list[float]]
    ) -> int:
        if not chunks:
            return 0

        collection = self.get_or_create_collection(repo_id)

        ids = [f"{repo_id}_{i}" for i in range(len(chunks))]
        documents = [c.text for c in chunks]
        metadatas = [
            {
                "file_path": c.file_path,
                "language": c.language,
                "start_line": c.start_line,
                "end_line": c.end_line,
                "chunk_type": c.chunk_type,
                "repo_id": repo_id
            }
            for c in chunks
        ]

        collection.upsert(
            ids=ids,
            documents=documents,
            embeddings=embeddings,
            metadatas=metadatas
        )

        log.info("chunks_stored", repo_id=repo_id, count=len(chunks))
        return len(chunks)

    def similarity_search(
        self,
        repo_id: str,
        query_embedding: list[float],
        k: int = 5,
        language_filter: str = None
    ) -> list[dict]:
        collection = self.get_or_create_collection(repo_id)

        where = {"repo_id": repo_id}
        if language_filter:
            where["language"] = language_filter

        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=min(k, collection.count()),
            where=where,
            include=["documents", "metadatas", "distances"]
        )

        if not results["ids"][0]:
            return []

        chunks = []
        for i, _ in enumerate(results["ids"][0]):
            chunks.append({
                "text": results["documents"][0][i],
                "metadata": results["metadatas"][0][i],
                "score": 1 - results["distances"][0][i]
            })

        return chunks

    def delete_collection(self, repo_id: str) -> bool:
        try:
            self.client.delete_collection(self._collection_name(repo_id))
            return True
        except Exception:
            return False

    def get_stats(self) -> dict:
        collections = self.client.list_collections()
        total_chunks = sum(c.count() for c in collections)
        return {
            "indexed_repos": len(collections),
            "total_chunks": total_chunks,
            "collections": [c.name for c in collections]
        }
