"""Retrieve the passages most similar to a question."""

from app.models import Chunk
from app.services.embeddings import cosine


def retrieve(
    chunks: list[Chunk],
    query_embedding: list[float],
    k: int,
) -> list[tuple[Chunk, float]]:
    if k <= 0 or not chunks:
        return []
    scored = [
        (chunk, cosine(query_embedding, list(chunk.embedding or []))) for chunk in chunks
    ]
    scored.sort(key=lambda item: item[1], reverse=True)
    return scored[:k]
