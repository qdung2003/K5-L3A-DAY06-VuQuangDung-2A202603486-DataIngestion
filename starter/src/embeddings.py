"""One real, revision-pinned Sentence Transformers model; errors propagate."""
import os
from pathlib import Path
from typing import Protocol

ROOT = Path(__file__).resolve().parents[2]
MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
MODEL_REVISION = "1110a243fdf4706b3f48f1d95db1a4f5529b4d41"


class Embedder(Protocol):
    model_name: str
    dimensions: int
    def embed_documents(self, texts: list[str]) -> list[list[float]]: ...
    def embed_query(self, question: str) -> list[float]: ...


class MyEmbedder:
    def __init__(self, model_name: str = MODEL_NAME, offline: bool = True) -> None:
        os.environ.setdefault("HF_HOME", str(ROOT / ".cache" / "huggingface"))
        os.environ.setdefault("HF_HUB_DISABLE_TELEMETRY", "1")
        if offline:
            os.environ["HF_HUB_OFFLINE"] = "1"
        from sentence_transformers import SentenceTransformer
        import torch
        torch.set_num_threads(4)
        self.model_name = model_name
        self.revision = MODEL_REVISION
        self.model = SentenceTransformer(str(ROOT / ".cache" / "all-MiniLM-L6-v2"),
            device="cpu", local_files_only=offline)
        self.dimensions = self.model.get_sentence_embedding_dimension()
        if self.dimensions != 384:
            raise ValueError(f"Unexpected model dimension: {self.dimensions}")

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return self.model.encode(texts, batch_size=32, normalize_embeddings=True,
            show_progress_bar=False, convert_to_numpy=True).tolist()

    def embed_query(self, question: str) -> list[float]:
        return self.embed_documents([question])[0]
