import re

from app.config import Settings
from app.models import AskResponse, Source
from app.rag.chunking import SECTION_NAMES
from app.rag.ollama import OllamaClient
from app.rag.store import VectorStore
from app.security.guardrails import validate_model_output

RISK_REFERENCE_PATTERN = re.compile(
    r"\b(?:llm|top|riesgo|numero|número|puesto|posicion|posición)\s*"
    r"(?:n(?:ro)?\.?\s*)?[#º°]?\s*0?(10|[1-9])\b",
    re.IGNORECASE,
)


def _referenced_section(question: str) -> str | None:
    match = RISK_REFERENCE_PATTERN.search(question)
    if match is None:
        return None
    identifier = f"LLM{int(match.group(1)):02d}:2026"
    return SECTION_NAMES.get(identifier)


class RagService:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.client = OllamaClient(
            base_url=settings.ollama_base_url,
            embedding_model=settings.embedding_model,
            llm_model=settings.llm_model,
            context_tokens=settings.model_context_tokens,
            output_tokens=settings.model_output_tokens,
        )
        self.store = VectorStore.load(settings.index_dir)

    def ask(self, question: str) -> AskResponse:
        section = _referenced_section(question)
        retrieval_query = (
            f"{question}\nSeccion solicitada: {section}" if section is not None else question
        )
        query_embedding = self.client.embed([retrieval_query])[0]
        retrieved = self.store.search(
            query_embedding=query_embedding,
            top_k=self.settings.retrieval_top_k,
            min_similarity=self.settings.min_similarity,
            section=section,
        )

        if not retrieved:
            return AskResponse(
                answer=(
                    "No encontre informacion suficientemente relacionada en el "
                    "documento OWASP Top 10 for LLM Applications 2026."
                ),
                sources=[],
            )

        context_parts: list[str] = []
        sources: list[Source] = []
        seen_sources: set[tuple[str, int]] = set()
        for chunk, score in retrieved:
            context_parts.append(
                f"[Documento: {chunk.document}; pagina: {chunk.page}; "
                f"seccion: {chunk.section}]\n{chunk.text}"
            )
            source_key = (chunk.document, chunk.page)
            if source_key not in seen_sources:
                sources.append(
                    Source(
                        document=chunk.document,
                        page=chunk.page,
                        section=chunk.section,
                        score=round(score, 4),
                    )
                )
                seen_sources.add(source_key)

        answer = validate_model_output(
            self.client.answer(question, "\n\n---\n\n".join(context_parts))
        )
        return AskResponse(answer=answer, sources=sources)
