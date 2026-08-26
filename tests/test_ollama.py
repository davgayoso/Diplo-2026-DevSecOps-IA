from typing import Any

import app.rag.ollama as ollama_module
from app.rag.ollama import OllamaClient


class FakeResponse:
    def __init__(self, payload: dict[str, Any]) -> None:
        self.payload = payload

    def raise_for_status(self) -> None:
        pass

    def json(self) -> dict[str, Any]:
        return self.payload


class FakeHttpClient:
    requests: list[tuple[str, dict[str, Any]]] = []

    def __init__(self, timeout: float) -> None:
        self.timeout = timeout

    def __enter__(self) -> "FakeHttpClient":
        return self

    def __exit__(self, *_args: object) -> None:
        pass

    def post(self, url: str, json: dict[str, Any]) -> FakeResponse:
        self.requests.append((url, json))
        if url.endswith("/api/embed"):
            return FakeResponse({"embeddings": [[0.1, 0.2]]})
        return FakeResponse({"message": {"content": " grounded answer "}})


def _client() -> OllamaClient:
    return OllamaClient(
        base_url="http://ollama:11434/",
        embedding_model="embedding-model",
        llm_model="language-model",
        context_tokens=4096,
        output_tokens=500,
    )


def test_embed_uses_configured_model(monkeypatch) -> None:
    FakeHttpClient.requests.clear()
    monkeypatch.setattr(ollama_module.httpx, "Client", FakeHttpClient)

    embeddings = _client().embed(["sample text"])

    assert embeddings == [[0.1, 0.2]]
    url, payload = FakeHttpClient.requests[0]
    assert url == "http://ollama:11434/api/embed"
    assert payload["model"] == "embedding-model"


def test_answer_marks_context_as_untrusted(monkeypatch) -> None:
    FakeHttpClient.requests.clear()
    monkeypatch.setattr(ollama_module.httpx, "Client", FakeHttpClient)

    answer = _client().answer("user question", "retrieved context")

    assert answer == "grounded answer"
    _, payload = FakeHttpClient.requests[0]
    assert payload["model"] == "language-model"
    assert "CONTEXTO NO CONFIABLE" in payload["messages"][1]["content"]
    assert "retrieved context" in payload["messages"][1]["content"]
    assert "user question" in payload["messages"][1]["content"]
