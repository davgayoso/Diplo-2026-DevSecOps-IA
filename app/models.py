from pydantic import BaseModel, Field, field_validator

from app.security.guardrails import normalize_question


class AskRequest(BaseModel):
    question: str = Field(min_length=3, max_length=1000)

    @field_validator("question")
    @classmethod
    def validate_question(cls, value: str) -> str:
        return normalize_question(value)


class Source(BaseModel):
    document: str
    page: int
    section: str
    score: float


class AskResponse(BaseModel):
    answer: str
    sources: list[Source]


class ReadyResponse(BaseModel):
    status: str
    chunks: int
    embedding_model: str
