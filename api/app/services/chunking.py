"""Split extracted text into overlapping passages for retrieval."""

from app.services.textutil import clean_text


def chunk_text(text: str, size: int = 700, overlap: int = 100) -> list[str]:
    """Pack paragraphs into chunks, then hard-split anything still too long.

    Overlap keeps a sentence that lands on a boundary available in both
    neighboring passages, so a question can still match it.
    """
    if size <= 0:
        raise ValueError("chunk size must be positive")
    overlap = max(0, min(overlap, size // 2))
    cleaned = clean_text(text)
    if not cleaned:
        return []

    paragraphs = [part.strip() for part in cleaned.split("\n\n") if part.strip()]
    packed: list[str] = []
    current = ""
    for paragraph in paragraphs:
        if len(paragraph) > size:
            if current:
                packed.append(current)
                current = ""
            packed.extend(_split_long(paragraph, size, overlap))
            continue
        candidate = f"{current}\n\n{paragraph}" if current else paragraph
        if len(candidate) <= size:
            current = candidate
        else:
            if current:
                packed.append(current)
            current = paragraph
    if current:
        packed.append(current)
    return packed


def _split_long(paragraph: str, size: int, overlap: int) -> list[str]:
    """Break on a sentence or a space so a passage never ends mid-word."""
    pieces: list[str] = []
    start = 0
    length = len(paragraph)
    while start < length:
        end = min(length, start + size)
        if end < length:
            end = _snap_end(paragraph, start, end)
        piece = paragraph[start:end].strip()
        if piece:
            pieces.append(piece)
        if end >= length:
            break
        next_start = end - overlap
        if next_start <= start:
            next_start = end
        else:
            next_start = _snap_start(paragraph, next_start, end)
            if next_start <= start:
                next_start = end
        start = next_start
    return pieces


def _snap_end(text: str, start: int, end: int) -> int:
    window = text[start:end]
    floor = max(0, len(window) // 2)
    for mark in (". ", "! ", "? ", ".\n", "!\n", "?\n"):
        index = window.rfind(mark, floor)
        if index != -1:
            return start + index + 1
    space = window.rfind(" ", floor)
    if space != -1:
        return start + space
    return end


def _snap_start(text: str, pos: int, limit: int) -> int:
    if pos <= 0:
        return 0
    if pos < len(text) and not text[pos - 1].isspace() and not text[pos].isspace():
        space = text.find(" ", pos, max(pos, limit) + 1)
        if space != -1:
            return space + 1
    while pos < len(text) and text[pos].isspace():
        pos += 1
    return pos
