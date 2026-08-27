import re
import unicodedata

OVERRIDE_PATTERNS = (
    re.compile(
        r"^(ignore|disregard|forget)\b.{0,60}\b(previous|prior|system)\b"
        r".{0,30}\b(instructions?|prompt)\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"^(ignora|ignorá|olvida|olvidá|omite)\b.{0,60}\b"
        r"(instrucciones|prompt)\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"^(reveal|show|print|expose|revela|mostrá|muestra|imprime)\b.{0,40}\b"
        r"(system prompt|prompt del sistema|instrucciones internas)\b",
        re.IGNORECASE,
    ),
)


def normalize_question(value: str) -> str:
    normalized = unicodedata.normalize("NFKC", value).strip()
    if any(
        unicodedata.category(character) in {"Cc", "Cf"} and character not in "\n\t"
        for character in normalized
    ):
        raise ValueError("Question contains unsupported control characters")

    normalized = re.sub(r"\s+", " ", normalized)
    if len(normalized) < 3:
        raise ValueError("Question must contain at least 3 characters")
    if any(pattern.search(normalized) for pattern in OVERRIDE_PATTERNS):
        raise ValueError("Question contains a disallowed instruction override")
    return normalized


def validate_model_output(value: str, max_characters: int = 8000) -> str:
    """Reject malformed model output before it crosses the API boundary."""
    normalized = unicodedata.normalize("NFKC", value).strip()
    if not normalized:
        raise ValueError("Model output must not be empty")
    if len(normalized) > max_characters:
        raise ValueError("Model output exceeds the allowed size")
    if any(
        unicodedata.category(character) in {"Cc", "Cf"} and character not in "\n\t"
        for character in normalized
    ):
        raise ValueError("Model output contains unsupported control characters")
    return normalized
