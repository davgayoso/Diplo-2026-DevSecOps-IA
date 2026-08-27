import json
from dataclasses import asdict
from pathlib import Path

import faiss
import numpy as np

from app.rag.chunking import Chunk


class VectorStore:
    def __init__(self, index: faiss.Index, chunks: list[Chunk]) -> None:
        self.index = index
        self.chunks = chunks

    @staticmethod
    def _normalize(vectors: list[list[float]]) -> np.ndarray:
        array = np.asarray(vectors, dtype="float32")
        faiss.normalize_L2(array)
        return array

    @classmethod
    def build(cls, chunks: list[Chunk], embeddings: list[list[float]]) -> "VectorStore":
        if not chunks or len(chunks) != len(embeddings):
            raise ValueError("chunks and embeddings must have the same non-zero length")

        vectors = cls._normalize(embeddings)
        index = faiss.IndexFlatIP(vectors.shape[1])
        index.add(vectors)
        return cls(index=index, chunks=chunks)

    def save(self, directory: Path, embedding_model: str, corpus_fingerprint: str) -> None:
        directory.mkdir(parents=True, exist_ok=True)
        faiss.write_index(self.index, str(directory / "index.faiss"))
        (directory / "chunks.json").write_text(
            json.dumps([asdict(chunk) for chunk in self.chunks], ensure_ascii=False),
            encoding="utf-8",
        )
        (directory / "manifest.json").write_text(
            json.dumps(
                {
                    "embedding_model": embedding_model,
                    "chunks": len(self.chunks),
                    "corpus_fingerprint": corpus_fingerprint,
                },
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )

    @classmethod
    def load(cls, directory: Path) -> "VectorStore":
        index = faiss.read_index(str(directory / "index.faiss"))
        raw_chunks = json.loads((directory / "chunks.json").read_text(encoding="utf-8"))
        chunks = [Chunk(**item) for item in raw_chunks]
        if index.ntotal != len(chunks):
            raise ValueError("FAISS index and chunk metadata are inconsistent")
        return cls(index=index, chunks=chunks)

    def search(
        self,
        query_embedding: list[float],
        top_k: int,
        min_similarity: float,
        section: str | None = None,
    ) -> list[tuple[Chunk, float]]:
        query = self._normalize([query_embedding])
        search_limit = len(self.chunks) if section else min(top_k, len(self.chunks))
        scores, positions = self.index.search(query, search_limit)
        results: list[tuple[Chunk, float]] = []
        for position, score in zip(positions[0], scores[0], strict=True):
            if position < 0 or float(score) < min_similarity:
                continue
            chunk = self.chunks[int(position)]
            if section is not None and chunk.section != section:
                continue
            results.append((chunk, float(score)))
            if len(results) == top_k:
                break
        return results
