import logging

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse


def _request_id(request: Request) -> str:
    return getattr(request.state, "request_id", "unavailable")


def _error_code(status_code: int) -> str:
    return {
        401: "authentication_required",
        403: "forbidden",
        429: "rate_limit_exceeded",
        503: "service_unavailable",
    }.get(status_code, "request_error")


def _response(
    request: Request,
    status_code: int,
    code: str,
    message: str,
    headers: dict[str, str] | None = None,
) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content={
            "error": {
                "code": code,
                "message": message,
                "request_id": _request_id(request),
            }
        },
        headers=headers,
    )


def register_error_handlers(application: FastAPI) -> None:
    logger = logging.getLogger("rag_api")

    @application.exception_handler(HTTPException)
    async def http_error(request: Request, error: HTTPException) -> JSONResponse:
        message = error.detail if isinstance(error.detail, str) else "The request was rejected."
        return _response(
            request,
            error.status_code,
            _error_code(error.status_code),
            message,
            error.headers,
        )

    @application.exception_handler(RequestValidationError)
    async def validation_error(request: Request, _error: RequestValidationError) -> JSONResponse:
        return _response(
            request,
            422,
            "validation_error",
            "The request body is invalid.",
        )

    @application.exception_handler(Exception)
    async def unexpected_error(request: Request, error: Exception) -> JSONResponse:
        logger.error(
            "unhandled_exception",
            extra={
                "request_id": _request_id(request),
                "error_type": type(error).__name__,
            },
        )
        return _response(
            request,
            500,
            "internal_error",
            "An unexpected error occurred.",
        )
