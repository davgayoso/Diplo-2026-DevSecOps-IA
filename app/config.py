import os
from dataclasses import dataclass
from pathlib import Path
from secrets import compare_digest


def _integer(name: str, default: int) -> int:
    return int(os.getenv(name, str(default)))


def _floating(name: str, default: float) -> float:
    return float(os.getenv(name, str(default)))


@dataclass(frozen=True)
class Settings:
    ollama_base_url: str = os.getenv("OLLAMA_BASE_URL", "http://ollama:11434")
    llm_model: str = os.getenv("LLM_MODEL", "llama3.2:3b")
    embedding_model: str = os.getenv("EMBEDDING_MODEL", "qwen3-embedding:0.6b")
    documents_dir: Path = Path(os.getenv("DOCUMENTS_DIR", "data/documents"))
    index_dir: Path = Path(os.getenv("INDEX_DIR", "data/index"))
    document_start_page: int = _integer("DOCUMENT_START_PAGE", 5)
    document_end_page: int = _integer("DOCUMENT_END_PAGE", 107)
    chunk_size_words: int = _integer("CHUNK_SIZE_WORDS", 220)
    chunk_overlap_words: int = _integer("CHUNK_OVERLAP_WORDS", 40)
    retrieval_top_k: int = _integer("RETRIEVAL_TOP_K", 6)
    min_similarity: float = _floating("MIN_SIMILARITY", 0.25)
    model_context_tokens: int = _integer("MODEL_CONTEXT_TOKENS", 4096)
    model_output_tokens: int = _integer("MODEL_OUTPUT_TOKENS", 500)
    reader_api_key: str = os.getenv("READER_API_KEY", "")
    admin_api_key: str = os.getenv("ADMIN_API_KEY", "")
    rate_limit_requests: int = _integer("RATE_LIMIT_REQUESTS", 10)
    rate_limit_window_seconds: int = _integer("RATE_LIMIT_WINDOW_SECONDS", 60)

    def validate_security(self) -> None:
        if len(self.reader_api_key) < 16 or len(self.admin_api_key) < 16:
            raise RuntimeError("API keys must contain at least 16 characters")
        if compare_digest(self.reader_api_key, self.admin_api_key):
            raise RuntimeError("Reader and admin API keys must be different")
        if self.rate_limit_requests < 1 or self.rate_limit_window_seconds < 1:
            raise RuntimeError("Rate limit values must be positive")


settings = Settings()
