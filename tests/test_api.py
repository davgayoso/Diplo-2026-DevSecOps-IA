from fastapi.testclient import TestClient

from app.main import create_app
from app.models import AskResponse, Source


class FakeStore:
    chunks = [object(), object()]


class FakeRagService:
    store = FakeStore()

    def __init__(self, _settings: object) -> None:
        pass

    def ask(self, question: str) -> AskResponse:
        return AskResponse(
            answer=f"Respuesta de prueba para: {question}",
            sources=[
                Source(
                    document="owasp.pdf",
                    page=10,
                    section="LLM01:2026 Prompt Injection",
                    score=0.91,
                )
            ],
        )


class FailingRagService(FakeRagService):
    def ask(self, question: str) -> AskResponse:
        raise RuntimeError(f"secret model error: {question}")


def test_health_and_readiness() -> None:
    with TestClient(create_app(FakeRagService)) as client:
        assert client.get("/health").json() == {"status": "ok"}
        response = client.get("/ready")

    assert response.status_code == 200
    assert response.json()["status"] == "ready"
    assert response.json()["chunks"] == 2


def test_ask_returns_answer_and_sources() -> None:
    with TestClient(create_app(FakeRagService)) as client:
        response = client.post("/ask", json={"question": "¿Qué es prompt injection?"})

    assert response.status_code == 200
    assert "prompt injection" in response.json()["answer"]
    assert response.json()["sources"][0]["page"] == 10


def test_ask_validates_question_length() -> None:
    with TestClient(create_app(FakeRagService)) as client:
        response = client.post("/ask", json={"question": "x"})

    assert response.status_code == 422


def test_ask_hides_internal_model_errors() -> None:
    with TestClient(create_app(FailingRagService)) as client:
        response = client.post("/ask", json={"question": "valid question"})

    assert response.status_code == 503
    assert response.json() == {"detail": "The local model service is temporarily unavailable."}
    assert "secret model error" not in response.text
