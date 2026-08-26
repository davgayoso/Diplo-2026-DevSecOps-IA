import json
from pathlib import Path
from types import SimpleNamespace

import pytest

import app.ingest as ingest_module
from app.rag.chunking import Chunk


def _settings(documents_dir: Path, index_dir: Path) -> SimpleNamespace:
    return SimpleNamespace(
        documents_dir=documents_dir,
        index_dir=index_dir,
        embedding_model="embedding-model",
        llm_model="language-model",
        ollama_base_url="http://ollama:11434",
        document_start_page=5,
        document_end_page=107,
        chunk_size_words=220,
        chunk_overlap_words=40,
        model_context_tokens=4096,
        model_output_tokens=500,
    )


def test_batches_preserve_all_items() -> None:
    chunks = [Chunk(str(index), "text", "doc.pdf", 1, "section") for index in range(5)]

    batches = ingest_module._batches(chunks, size=2)

    assert [len(batch) for batch in batches] == [2, 2, 1]


def test_index_is_current_checks_manifest_and_files(tmp_path: Path, monkeypatch) -> None:
    index_dir = tmp_path / "index"
    index_dir.mkdir()
    monkeypatch.setattr(ingest_module, "settings", _settings(tmp_path, index_dir))

    assert ingest_module._index_is_current("expected") is False

    (index_dir / "index.faiss").write_bytes(b"index")
    (index_dir / "chunks.json").write_text("[]", encoding="utf-8")
    (index_dir / "manifest.json").write_text(
        json.dumps({"corpus_fingerprint": "expected"}), encoding="utf-8"
    )

    assert ingest_module._index_is_current("expected") is True
    assert ingest_module._index_is_current("different") is False


def test_ingestion_builds_and_saves_index(tmp_path: Path, monkeypatch, capsys) -> None:
    documents_dir = tmp_path / "documents"
    index_dir = tmp_path / "index"
    documents_dir.mkdir()
    (documents_dir / "sample.pdf").write_bytes(b"sample document")
    settings = _settings(documents_dir, index_dir)
    monkeypatch.setattr(ingest_module, "settings", settings)

    chunk = Chunk("a", "sample text", "sample.pdf", 5, "section")
    monkeypatch.setattr(ingest_module, "chunks_from_pdf", lambda *_args, **_kwargs: [chunk])

    class FakeClient:
        def __init__(self, **_kwargs) -> None:
            pass

        def embed(self, texts: list[str]) -> list[list[float]]:
            assert texts == ["sample text"]
            return [[1.0, 0.0]]

    saved: dict[str, object] = {}

    class FakeStore:
        def save(self, directory: Path, model: str, fingerprint: str) -> None:
            saved.update(directory=directory, model=model, fingerprint=fingerprint)

    class FakeVectorStore:
        @classmethod
        def build(cls, chunks, embeddings) -> FakeStore:
            assert chunks == [chunk]
            assert embeddings == [[1.0, 0.0]]
            return FakeStore()

    monkeypatch.setattr(ingest_module, "OllamaClient", FakeClient)
    monkeypatch.setattr(ingest_module, "VectorStore", FakeVectorStore)

    ingest_module.main()

    assert saved["directory"] == index_dir
    assert saved["model"] == "embedding-model"
    assert "Indexed 1 chunks" in capsys.readouterr().out


def test_ingestion_rejects_missing_pdf_directory(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(ingest_module, "settings", _settings(tmp_path, tmp_path / "index"))

    with pytest.raises(RuntimeError, match="No PDF files"):
        ingest_module.main()
