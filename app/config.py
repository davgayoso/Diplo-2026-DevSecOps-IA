from dataclasses import dataclass
from pathlib import Path
import os


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


settings = Settings()
