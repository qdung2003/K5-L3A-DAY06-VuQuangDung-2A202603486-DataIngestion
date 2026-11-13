"""Persistent Chroma cosine HNSW, validated vectors and native metadata filters."""
import math
from pathlib import Path
from typing import Any
import chromadb
from chromadb.config import Settings
from .models import Chunk

FILTER_FIELDS = {"section", "version", "language"}


class ChromaStore:
    def __init__(self, path: str | Path, dimensions: int) -> None:
        if dimensions < 1:
            raise ValueError("dimensions must be positive")
        self.dimensions = dimensions
        self.client = chromadb.PersistentClient(path=str(path),
            settings=Settings(anonymized_telemetry=False))

    def create_schema(self) -> None:
        for strategy in "ABC":
            self.client.get_or_create_collection(f"day06_{strategy.lower()}",
                metadata={"hnsw:space": "cosine", "hnsw:search_ef": 100,
                          "embedding_dimensions": self.dimensions}, embedding_function=None)

    def collection(self, strategy: str):
        if strategy not in {"A", "B", "C"}:
            raise ValueError("Unknown strategy")
        return self.client.get_collection(f"day06_{strategy.lower()}", embedding_function=None)

    def validate_vectors(self, vectors):
        for vector in vectors:
            if len(vector) != self.dimensions or not all(math.isfinite(x) for x in vector):
                raise ValueError("Vector dimension mismatch or non-finite value")
            if not any(vector):
                raise ValueError("Zero vectors are not supported for cosine search")

    def upsert(self, strategy: str, chunks: list[Chunk], vectors: list[list[float]]) -> None:
        if len(chunks) != len(vectors):
            raise ValueError("chunks/vectors length mismatch")
        ids = [c.chunk_id for c in chunks]
        if len(ids) != len(set(ids)):
            raise ValueError("Duplicate chunk IDs")
        self.validate_vectors(vectors)
        collection = self.collection(strategy)
        # Snapshot reconciliation removes chunks of changed and deleted documents.
        # Upsert first; retry after interruption converges to the supplied snapshot.
        for start in range(0, len(chunks), 128):
            batch = chunks[start:start + 128]
            collection.upsert(ids=ids[start:start + 128],
                embeddings=vectors[start:start + 128], documents=[c.text for c in batch],
                metadatas=[{**c.metadata, "document_id": c.document_id,
                            "source": c.source, "page": c.page} for c in batch])
        old = set(collection.get(include=[])["ids"]) - set(ids)
        if old:
            collection.delete(ids=sorted(old))

    def search(self, strategy: str, query_vector: list[float], top_k: int = 3,
               filters: dict[str, Any] | None = None) -> list[dict[str, Any]]:
        self.validate_vectors([query_vector])
        if top_k < 1:
            raise ValueError("top_k must be positive")
        where = None
        if filters:
            if set(filters) - FILTER_FIELDS or any(not isinstance(v, str) for v in filters.values()):
                raise ValueError("Unsupported filter field or value type")
            clauses = [{k: {"$eq": v}} for k, v in filters.items()]
            where = clauses[0] if len(clauses) == 1 else {"$and": clauses}
        result = self.collection(strategy).query(query_embeddings=[query_vector],
            n_results=top_k, where=where, include=["documents", "metadatas", "distances"])
        return [{"chunk_id": cid, "text": text, "metadata": meta,
                 "score": 1 - distance, "cosine_distance": distance}
                for cid, text, meta, distance in zip(result["ids"][0], result["documents"][0],
                    result["metadatas"][0], result["distances"][0])]
