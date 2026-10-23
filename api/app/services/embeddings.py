"""Local embeddings that do not call a model API.

Each token is hashed into a fixed bucket with a sign. The vector is L2
normalized so cosine similarity is a dot product. Texts that share words land
closer together, which is enough for passage retrieval in a résumé demo and
for tests that must run with no network.

Set EMBEDDING_PROVIDER=openai to use a hosted embedding model instead. The
document records which space its chunks were stored in, and queries use that
same space.
"""

import hashlib
import math

from app.services.textutil import tokenize

EMBEDDING_DIM = 256


def local_embed(texts: list[str], dim: int = EMBEDDING_DIM) -> list[list[float]]:
    return [_embed_one(text, dim) for text in texts]


def cosine(left: list[float], right: list[float]) -> float:
    if len(left) != len(right) or not left:
        return 0.0
    return float(sum(a * b for a, b in zip(left, right, strict=True)))


def _embed_one(text: str, dim: int) -> list[float]:
    vector = [0.0] * dim
    for token in tokenize(text):
        digest = hashlib.sha1(token.encode("utf-8")).digest()
        bucket = int.from_bytes(digest[:4], "big") % dim
        sign = 1.0 if digest[4] % 2 == 0 else -1.0
        vector[bucket] += sign
    norm = math.sqrt(sum(value * value for value in vector))
    if norm == 0:
        return vector
    return [value / norm for value in vector]
