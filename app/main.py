from collections.abc import Callable
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request, status

from app.config import Settings, settings
from app.models import AskRequest, AskResponse, ReadyResponse
from app.rag.service import RagService

RagFactory = Callable[[Settings], RagService]


def create_app(rag_factory: RagFactory = RagService) -> FastAPI:
    @asynccontextmanager
    async def lifespan(application: FastAPI):
        application.state.rag = rag_factory(settings)
        yield

    application = FastAPI(
        title="OWASP LLM Top 10 RAG API",
        description="API local para consultar el OWASP Top 10 para aplicaciones con LLM.",
        version="0.2.0",
        lifespan=lifespan,
    )

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
            embedding_model=settings.embedding_model,
        )

    @application.post("/ask", response_model=AskResponse, tags=["rag"])
    def ask(payload: AskRequest, request: Request) -> AskResponse:
        rag: RagService = request.app.state.rag
        try:
            return rag.ask(payload.question)
        except Exception as error:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="The local model service is temporarily unavailable.",
            ) from error

    return application


app = create_app()
