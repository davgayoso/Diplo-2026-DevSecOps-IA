from collections.abc import Callable
from contextlib import asynccontextmanager
from time import monotonic
from typing import Annotated

from fastapi import FastAPI, HTTPException, Request, Response, Security, status

from app.config import Settings, settings
from app.errors import register_error_handlers
from app.models import AskRequest, AskResponse, ReadyResponse
from app.observability.logging import configure_logging
from app.observability.metrics import Metrics
from app.observability.middleware import install_observability
from app.rag.service import RagService
from app.security.auth import ApiKeyAuthenticator, Principal
from app.security.headers import install_security_headers
from app.security.rate_limit import InMemoryRateLimiter

RagFactory = Callable[[Settings], RagService]


def create_app(
    rag_factory: RagFactory = RagService,
    application_settings: Settings = settings,
    clock: Callable[[], float] = monotonic,
) -> FastAPI:
    configure_logging()
    metrics = Metrics()
    authenticator = ApiKeyAuthenticator(application_settings)
    rate_limiter = InMemoryRateLimiter(
        limit=application_settings.rate_limit_requests,
        window_seconds=application_settings.rate_limit_window_seconds,
        clock=clock,
    )

    @asynccontextmanager
    async def lifespan(application: FastAPI):
        application_settings.validate_security()
        application.state.rag = rag_factory(application_settings)
        yield

    application = FastAPI(
        title="OWASP LLM Top 10 RAG API",
        description="API local para consultar el OWASP Top 10 para aplicaciones con LLM.",
        version="1.0.1",
        lifespan=lifespan,
    )
    register_error_handlers(application)
    install_security_headers(application)
    install_observability(application, metrics)

    async def require_admin(
        principal: Annotated[Principal, Security(authenticator)],
    ) -> Principal:
        if principal.role != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Administrator access is required.",
            )
        return principal

    @application.get("/health", tags=["system"])
    def health_check() -> dict[str, str]:
        """Report whether the HTTP service is running."""
        return {"status": "ok"}

    @application.get("/ready", response_model=ReadyResponse, tags=["system"])
    def readiness_check(request: Request) -> ReadyResponse:
        rag: RagService = request.app.state.rag
        return ReadyResponse(
            status="ready",
            chunks=len(rag.store.chunks),
            embedding_model=application_settings.embedding_model,
        )

    @application.post("/ask", response_model=AskResponse, tags=["rag"])
    def ask(
        payload: AskRequest,
        request: Request,
        principal: Annotated[Principal, Security(authenticator)],
    ) -> AskResponse:
        retry_after = rate_limiter.check(principal.client_id)
        if retry_after is not None:
            metrics.record_rate_limit_block(principal.client_id)
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Rate limit exceeded.",
                headers={"Retry-After": str(retry_after)},
            )

        rag: RagService = request.app.state.rag
        try:
            return rag.ask(payload.question)
        except Exception as error:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="The local model service is temporarily unavailable.",
            ) from error

    @application.get("/metrics", tags=["system"])
    def prometheus_metrics(
        _principal: Annotated[Principal, Security(require_admin)],
    ) -> Response:
        return Response(
            content=metrics.render(),
            headers={"Content-Type": metrics.content_type},
        )

    return application


app = create_app()
