from pathlib import Path
from types import SimpleNamespace

import app.rag.service as service_module
from app.rag.chunking import Chunk
from app.rag.service import RagService


class FakeClient:
    def __init__(self) -> None:
        self.context = ""

    def embed(self, _texts: list[str]) -> list[list[float]]:
        return [[1.0, 0.0]]

    def answer(self, _question: str, context: str) -> str:
        self.context = context
        return "grounded answer"


class FakeStore:
    def __init__(self, results: list[tuple[Chunk, float]]) -> None:
        self.results = results

    def search(self, **_kwargs) -> list[tuple[Chunk, float]]:
        return self.results


def _settings() -> SimpleNamespace:
    return SimpleNamespace(
        ollama_base_url="http://ollama:11434",
        embedding_model="embedding-model",
        llm_model="language-model",
        model_context_tokens=4096,
        model_output_tokens=500,
        index_dir=Path("data/index"),
        retrieval_top_k=6,
        min_similarity=0.25,
    )


def _service(monkeypatch, results: list[tuple[Chunk, float]]) -> RagService:
    fake_client = FakeClient()
    fake_store = FakeStore(results)
    monkeypatch.setattr(service_module, "OllamaClient", lambda **_kwargs: fake_client)
    monkeypatch.setattr(service_module.VectorStore, "load", lambda _path: fake_store)
    return RagService(_settings())


def test_service_returns_fallback_without_relevant_chunks(monkeypatch) -> None:
    service = _service(monkeypatch, [])

    response = service.ask("unrelated question")

    assert response.sources == []
    assert "No encontre informacion" in response.answer


def test_service_builds_context_and_deduplicates_sources(monkeypatch) -> None:
    first = Chunk("a", "first text", "owasp.pdf", 10, "LLM01")
    second = Chunk("b", "second text", "owasp.pdf", 10, "LLM01")
    service = _service(monkeypatch, [(first, 0.91234), (second, 0.8)])

    response = service.ask("What is prompt injection?")

    assert response.answer == "grounded answer"
    assert len(response.sources) == 1
    assert response.sources[0].score == 0.9123
    assert "first text" in service.client.context
    assert "second text" in service.client.context
