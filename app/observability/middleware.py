import logging
import re
from collections.abc import Awaitable, Callable
from time import monotonic
from uuid import uuid4

from fastapi import FastAPI, Request, Response

from app.observability.metrics import Metrics

REQUEST_ID_PATTERN = re.compile(r"^[A-Za-z0-9._-]{1,64}$")


def install_observability(application: FastAPI, metrics: Metrics) -> None:
    logger = logging.getLogger("rag_api")

    @application.middleware("http")
    async def observe_request(
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        supplied_request_id = request.headers.get("X-Request-ID", "")
        request_id = (
            supplied_request_id
            if REQUEST_ID_PATTERN.fullmatch(supplied_request_id)
            else uuid4().hex
        )
        request.state.request_id = request_id
        started_at = monotonic()
        response = await call_next(request)
        duration_seconds = monotonic() - started_at
        route = getattr(request.scope.get("route"), "path", request.url.path)
        metrics.observe_request(request.method, route, response.status_code, duration_seconds)
        logger.info(
            "request_completed",
            extra={
                "request_id": request_id,
                "method": request.method,
                "path": route,
                "status_code": response.status_code,
                "duration_ms": round(duration_seconds * 1000, 2),
                "client_id": getattr(request.state, "client_id", None),
                "role": getattr(request.state, "role", None),
            },
        )
        response.headers["X-Request-ID"] = request_id
        return response
