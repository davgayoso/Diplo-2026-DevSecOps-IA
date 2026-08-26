from pydantic import BaseModel, Field


class AskRequest(BaseModel):
    question: str = Field(min_length=3, max_length=1000)


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
