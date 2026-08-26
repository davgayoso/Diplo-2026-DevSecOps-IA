import re
from dataclasses import asdict, dataclass
from hashlib import sha256
from pathlib import Path

from pypdf import PdfReader

SECTION_PATTERN = re.compile(r"LLM(?:0[1-9]|10):2026")
SECTION_NAMES = {
    "LLM01:2026": "LLM01:2026 Prompt Injection",
    "LLM02:2026": "LLM02:2026 Sensitive Information Disclosure",
    "LLM03:2026": "LLM03:2026 Excessive Agency",
    "LLM04:2026": "LLM04:2026 Supply Chain",
    "LLM05:2026": "LLM05:2026 Data and Model Poisoning",
    "LLM06:2026": "LLM06:2026 Unbounded Consumption",
    "LLM07:2026": "LLM07:2026 Misinformation",
    "LLM08:2026": "LLM08:2026 Hidden Context Exposure",
    "LLM09:2026": "LLM09:2026 Vector and Embedding Weaknesses",
    "LLM10:2026": "LLM10:2026 Improper Output Handling",
}


@dataclass(frozen=True)
class Chunk:
    id: str
    text: str
    document: str
    page: int
    section: str

    def to_dict(self) -> dict[str, str | int]:
        return asdict(self)


def _clean_text(text: str) -> str:
    text = text.replace("\u00ad", "")
    text = re.sub(r"(?<=\w)-\s*\n\s*(?=\w)", "", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def _split_words(text: str, size: int, overlap: int) -> list[str]:
    if overlap >= size:
        raise ValueError("chunk overlap must be smaller than chunk size")

    words = text.split()
    if not words:
        return []

    chunks: list[str] = []
    step = size - overlap
    for start in range(0, len(words), step):
        piece = words[start : start + size]
        if piece:
            chunks.append(" ".join(piece))
        if start + size >= len(words):
            break
    return chunks


def chunks_from_pdf(
    path: Path,
    size: int,
    overlap: int,
    start_page: int = 1,
    end_page: int | None = None,
) -> list[Chunk]:
    document_hash = sha256(path.read_bytes()).hexdigest()[:12]
    reader = PdfReader(path)
    current_section = "Front matter"
    chunks: list[Chunk] = []

    for page_number, page in enumerate(reader.pages, start=1):
        if page_number < start_page:
            continue
        if end_page is not None and page_number > end_page:
            break

        raw_text = page.extract_text() or ""
        page_heading = _clean_text(raw_text[:130])
        match = SECTION_PATTERN.search(page_heading)
        if match:
            current_section = SECTION_NAMES[match.group(0)]
        elif "Appendix A: Related Framework Mappings" in page_heading:
            current_section = "Appendix A: Related Framework Mappings"
        elif "Appendix B: LLM Application Architecture" in page_heading:
            current_section = "Appendix B: LLM Application Architecture and Threat Modeling"
        elif re.search(r"\bReferences\b", page_heading):
            current_section = "References"

        clean_text = _clean_text(raw_text)
        for index, text in enumerate(_split_words(clean_text, size, overlap)):
            chunks.append(
                Chunk(
                    id=f"{document_hash}-p{page_number}-c{index}",
                    text=text,
                    document=path.name,
                    page=page_number,
                    section=current_section,
                )
            )

    return chunks
