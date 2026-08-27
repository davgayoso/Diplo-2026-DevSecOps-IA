from dataclasses import replace

import pytest
from fastapi.testclient import TestClient

from app.config import Settings
from app.main import create_app
from app.models import AskResponse, Source

READER_HEADERS = {"X-API-Key": "reader-test-key-1234567890"}
ADMIN_HEADERS = {"X-API-Key": "admin-test-key-1234567890"}


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


def test_health_and_readiness_are_public(secure_settings: Settings) -> None:
    with TestClient(create_app(FakeRagService, secure_settings)) as client:
        health = client.get("/health", headers={"X-Request-ID": "test-request-1"})
        ready = client.get("/ready")

    assert health.json() == {"status": "ok"}
    assert health.headers["X-Request-ID"] == "test-request-1"
    assert ready.status_code == 200
    assert ready.json()["status"] == "ready"
    assert ready.json()["chunks"] == 2


def test_security_headers_are_added_to_success_and_error_responses(
    secure_settings: Settings,
) -> None:
    with TestClient(create_app(FakeRagService, secure_settings)) as client:
        success = client.get("/health")
        authentication_error = client.post(
            "/ask",
            json={"question": "valid question"},
        )

    for response in (success, authentication_error):
        assert response.headers["X-Content-Type-Options"] == "nosniff"
        assert response.headers["Cross-Origin-Resource-Policy"] == "same-origin"
        assert response.headers["Cache-Control"] == "no-store"


def test_ask_accepts_reader_key(secure_settings: Settings) -> None:
    with TestClient(create_app(FakeRagService, secure_settings)) as client:
        response = client.post(
            "/ask",
            json={"question": "¿Qué es prompt injection?"},
            headers=READER_HEADERS,
        )

    assert response.status_code == 200
    assert "prompt injection" in response.json()["answer"]
    assert response.json()["sources"][0]["page"] == 10


@pytest.mark.parametrize(
    "headers",
    [{}, {"X-API-Key": "invalid-api-key-value"}],
)
def test_ask_rejects_missing_or_invalid_key(
    secure_settings: Settings, headers: dict[str, str]
) -> None:
    with TestClient(create_app(FakeRagService, secure_settings)) as client:
        response = client.post(
            "/ask",
            json={"question": "valid question"},
            headers=headers,
        )

    assert response.status_code == 401
    assert response.headers["WWW-Authenticate"] == "ApiKey"
    assert response.json()["error"]["code"] == "authentication_required"
    assert "request_id" in response.json()["error"]


def test_ask_returns_uniform_validation_error(secure_settings: Settings) -> None:
    with TestClient(create_app(FakeRagService, secure_settings)) as client:
        response = client.post(
            "/ask",
            json={"question": "x"},
            headers=READER_HEADERS,
        )

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "validation_error"
    assert response.json()["error"]["message"] == "The request body is invalid."


def test_ask_hides_internal_model_errors(secure_settings: Settings) -> None:
    with TestClient(create_app(FailingRagService, secure_settings)) as client:
        response = client.post(
            "/ask",
            json={"question": "valid question"},
            headers=READER_HEADERS,
        )

    assert response.status_code == 503
    assert response.json()["error"]["code"] == "service_unavailable"
    assert "secret model error" not in response.text


def test_metrics_requires_admin_role(secure_settings: Settings) -> None:
    with TestClient(create_app(FakeRagService, secure_settings)) as client:
        reader_response = client.get("/metrics", headers=READER_HEADERS)
        admin_response = client.get("/metrics", headers=ADMIN_HEADERS)

    assert reader_response.status_code == 403
    assert reader_response.json()["error"]["code"] == "forbidden"
    assert admin_response.status_code == 200
    assert "rag_api_http_requests_total" in admin_response.text


def test_rate_limit_returns_retry_after(secure_settings: Settings) -> None:
    limited_settings = replace(secure_settings, rate_limit_requests=2)
    with TestClient(create_app(FakeRagService, limited_settings, clock=lambda: 100.0)) as client:
        first = client.post("/ask", json={"question": "first question"}, headers=READER_HEADERS)
        second = client.post("/ask", json={"question": "second question"}, headers=READER_HEADERS)
        blocked = client.post("/ask", json={"question": "third question"}, headers=READER_HEADERS)

    assert first.status_code == 200
    assert second.status_code == 200
    assert blocked.status_code == 429
    assert blocked.headers["Retry-After"] == "60"
    assert blocked.json()["error"]["code"] == "rate_limit_exceeded"


def test_startup_rejects_missing_keys(secure_settings: Settings) -> None:
    invalid_settings = replace(secure_settings, reader_api_key="", admin_api_key="")

    with (
        pytest.raises(RuntimeError, match="at least 16 characters"),
        TestClient(create_app(FakeRagService, invalid_settings)),
    ):
        pass
