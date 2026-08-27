from dataclasses import dataclass
from secrets import compare_digest
from typing import Annotated, Literal

from fastapi import HTTPException, Request, Security, status
from fastapi.security import APIKeyHeader

from app.config import Settings

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


@dataclass(frozen=True)
class Principal:
    client_id: str
    role: Literal["reader", "admin"]


class ApiKeyAuthenticator:
    def __init__(self, settings: Settings) -> None:
        self.reader_api_key = settings.reader_api_key
        self.admin_api_key = settings.admin_api_key

    async def __call__(
        self,
        request: Request,
        api_key: Annotated[str | None, Security(api_key_header)] = None,
    ) -> Principal:
        if api_key is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="A valid API key is required.",
                headers={"WWW-Authenticate": "ApiKey"},
            )

        reader_match = compare_digest(api_key, self.reader_api_key)
        admin_match = compare_digest(api_key, self.admin_api_key)
        if not reader_match and not admin_match:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="A valid API key is required.",
                headers={"WWW-Authenticate": "ApiKey"},
            )

        principal = Principal(
            client_id="admin" if admin_match else "reader",
            role="admin" if admin_match else "reader",
        )
        request.state.client_id = principal.client_id
        request.state.role = principal.role
        return principal
