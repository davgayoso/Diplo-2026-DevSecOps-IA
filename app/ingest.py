from pathlib import Path
from hashlib import sha256
import json

from app.config import settings
from app.rag.chunking import Chunk, chunks_from_pdf
from app.rag.ollama import OllamaClient
from app.rag.store import VectorStore


def _batches(items: list[Chunk], size: int = 16) -> list[list[Chunk]]:
    return [items[start : start + size] for start in range(0, len(items), size)]


def _corpus_fingerprint(pdf_paths: list[Path]) -> str:
    digest = sha256()
    digest.update(settings.embedding_model.encode())
    digest.update(str(settings.document_start_page).encode())
    digest.update(str(settings.document_end_page).encode())
    digest.update(str(settings.chunk_size_words).encode())
    digest.update(str(settings.chunk_overlap_words).encode())
    for path in pdf_paths:
        digest.update(path.name.encode())
        digest.update(path.read_bytes())
    return digest.hexdigest()


def _index_is_current(fingerprint: str) -> bool:
    manifest_path = settings.index_dir / "manifest.json"
    index_path = settings.index_dir / "index.faiss"
    chunks_path = settings.index_dir / "chunks.json"
    if not (manifest_path.exists() and index_path.exists() and chunks_path.exists()):
        return False

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    return manifest.get("corpus_fingerprint") == fingerprint


def main() -> None:
    pdf_paths = sorted(Path(settings.documents_dir).glob("*.pdf"))
    if not pdf_paths:
        raise RuntimeError(f"No PDF files found in {settings.documents_dir}")

    fingerprint = _corpus_fingerprint(pdf_paths)
    if _index_is_current(fingerprint):
        print("The existing FAISS index matches the corpus; ingestion was skipped.")
        return

    chunks: list[Chunk] = []
    for path in pdf_paths:
        chunks.extend(
            chunks_from_pdf(
                path,
                size=settings.chunk_size_words,
                overlap=settings.chunk_overlap_words,
                start_page=settings.document_start_page,
                end_page=settings.document_end_page,
            )
        )

    client = OllamaClient(
        base_url=settings.ollama_base_url,
        embedding_model=settings.embedding_model,
        llm_model=settings.llm_model,
        context_tokens=settings.model_context_tokens,
        output_tokens=settings.model_output_tokens,
    )
    embeddings: list[list[float]] = []
    for batch in _batches(chunks):
        embeddings.extend(client.embed([chunk.text for chunk in batch]))

    store = VectorStore.build(chunks, embeddings)
    store.save(settings.index_dir, settings.embedding_model, fingerprint)
    print(f"Indexed {len(chunks)} chunks from {len(pdf_paths)} PDF file(s).")


if __name__ == "__main__":
    main()
