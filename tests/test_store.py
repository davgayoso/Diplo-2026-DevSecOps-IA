from pathlib import Path

import pytest

from app.rag.chunking import Chunk
from app.rag.store import VectorStore


def _chunks() -> list[Chunk]:
    return [
        Chunk("a", "prompt injection", "owasp.pdf", 10, "LLM01"),
        Chunk("b", "sensitive disclosure", "owasp.pdf", 18, "LLM02"),
    ]


def test_store_round_trip_and_similarity_search(tmp_path: Path) -> None:
    store = VectorStore.build(_chunks(), [[1.0, 0.0], [0.0, 1.0]])
    store.save(tmp_path, "test-model", "fingerprint")

    loaded = VectorStore.load(tmp_path)
    results = loaded.search([0.9, 0.1], top_k=2, min_similarity=0.0)

    assert loaded.index.ntotal == 2
    assert results[0][0].id == "a"
    assert results[0][1] > results[1][1]


def test_store_rejects_mismatched_embeddings() -> None:
    with pytest.raises(ValueError, match="same non-zero length"):
        VectorStore.build(_chunks(), [[1.0, 0.0]])
