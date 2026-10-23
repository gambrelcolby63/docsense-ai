"""Small text helpers shared by chunking, embeddings, and the mock model."""

import re

STOPWORDS = {
    "a",
    "an",
    "and",
    "are",
    "as",
    "at",
    "be",
    "by",
    "for",
    "from",
    "how",
    "in",
    "is",
    "it",
    "of",
    "on",
    "or",
    "that",
    "the",
    "this",
    "to",
    "was",
    "what",
    "when",
    "where",
    "which",
    "who",
    "why",
    "with",
    "does",
    "do",
    "about",
}


def clean_text(text: str) -> str:
    """Normalize whitespace and rejoin lines that a PDF or OCR pass wrapped."""
    text = text.replace("\x00", "")
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    lines = [re.sub(r"[ \t]+", " ", line).strip() for line in text.split("\n")]
    paragraphs: list[str] = []
    buffer = ""
    for line in lines:
        if not line:
            if buffer:
                paragraphs.append(buffer)
                buffer = ""
            continue
        if not buffer:
            buffer = line
            continue
        if _continues_line(buffer, line):
            if buffer.endswith("-") and line[0].islower():
                buffer = buffer[:-1] + line
            else:
                buffer = f"{buffer} {line}"
        else:
            paragraphs.append(buffer)
            buffer = line
    if buffer:
        paragraphs.append(buffer)
    return "\n\n".join(paragraphs).strip()


def _continues_line(previous: str, line: str) -> bool:
    if previous.endswith("-"):
        return True
    if previous[-1] in ".!?":
        return False
    return line[0].islower() or line[0].isdigit()


def tokenize(text: str) -> list[str]:
    found = re.findall(r"[a-z0-9]+", text.lower())
    return [tok for tok in found if tok not in STOPWORDS and len(tok) > 1]


def split_sentences(text: str) -> list[str]:
    sentences: list[str] = []
    for paragraph in re.split(r"\n\s*\n", text.strip()):
        parts = re.split(r"(?<=[.!?])\s+", paragraph.strip())
        sentences.extend(part.strip() for part in parts if part.strip())
    return sentences
