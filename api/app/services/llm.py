"""Pluggable chat completion.

`auto` uses the mock provider when OPENAI_API_KEY is empty, so tests and the
Docker demo stay free. Any OpenAI-compatible server (OpenAI, Groq, OpenRouter,
Ollama) works by changing the base URL and model name.
"""

import json
import logging
import re
from typing import Protocol

import httpx

from app.config import Settings
from app.services.embeddings import local_embed
from app.services.textutil import split_sentences, tokenize

logger = logging.getLogger(__name__)

SUMMARY_SYSTEM = (
    "You summarize one document for a study tool. Reply with JSON only, no markdown, "
    'in this shape: {"summary": "one short paragraph", "key_points": ["point", "point"]}. '
    "Use only facts from the document. Do not invent names, numbers, or dates. "
    "Write 3 to 6 key points."
)

ANSWER_SYSTEM = (
    "You answer a question using only the numbered passages from one document. "
    "Cite a passage you use with its number, like [1]. "
    "If the passages do not contain the answer, say you cannot find it in the document. "
    "Do not use outside knowledge."
)


class LLMError(Exception):
    """The language model request failed or returned something we cannot use."""


class LLMProvider(Protocol):
    name: str

    def complete(self, messages: list[dict[str, str]], *, temperature: float = 0.2) -> str: ...

    def embed_remote(self, texts: list[str]) -> list[list[float]]: ...


class MockProvider:
    """Deterministic stand-in. Summaries are extractive. Answers quote the source."""

    name = "mock"

    def complete(self, messages: list[dict[str, str]], *, temperature: float = 0.2) -> str:
        user_messages = [
            message["content"] for message in messages if message["role"] == "user"
        ]
        user = user_messages[-1] if user_messages else ""
        if "key_points" in " ".join(message["content"] for message in messages):
            summary, points = summarize_extractive(user)
            return json.dumps({"summary": summary, "key_points": points})
        return answer_extractive(user, [])

    def embed_remote(self, texts: list[str]) -> list[list[float]]:
        raise LLMError("The mock provider does not call a remote embedding model.")


class OpenAICompatibleProvider:
    name = "openai"

    def __init__(
        self,
        *,
        api_key: str,
        base_url: str,
        model: str,
        embedding_model: str,
        timeout: float = 60.0,
        http_client: httpx.Client | None = None,
    ) -> None:
        self.model = model
        self.embedding_model = embedding_model
        self._owns_client = http_client is None
        self._client = http_client or httpx.Client(
            base_url=base_url.rstrip("/"),
            headers={"Authorization": f"Bearer {api_key}"},
            timeout=timeout,
        )

    def close(self) -> None:
        if self._owns_client:
            self._client.close()

    def complete(self, messages: list[dict[str, str]], *, temperature: float = 0.2) -> str:
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": 800,
        }
        try:
            response = self._client.post("/chat/completions", json=payload)
            response.raise_for_status()
            body = response.json()
            return str(body["choices"][0]["message"]["content"])
        except (httpx.HTTPError, KeyError, IndexError, TypeError, ValueError) as exc:
            raise LLMError(f"The language model request failed: {exc}") from exc

    def embed_remote(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []
        try:
            response = self._client.post(
                "/embeddings",
                json={"model": self.embedding_model, "input": texts},
            )
            response.raise_for_status()
            rows = response.json()["data"]
            ordered = sorted(rows, key=lambda row: row.get("index", 0))
            vectors = [list(row["embedding"]) for row in ordered]
        except (httpx.HTTPError, KeyError, TypeError, ValueError) as exc:
            raise LLMError(f"The embedding request failed: {exc}") from exc
        if len(vectors) != len(texts):
            raise LLMError("The embedding endpoint returned an unexpected number of vectors.")
        return vectors


def build_provider(settings: Settings) -> LLMProvider:
    mode = settings.llm_provider.strip().lower()
    if mode == "auto":
        mode = "openai" if settings.openai_api_key.strip() else "mock"
    if mode == "mock":
        return MockProvider()
    if mode == "openai":
        if not settings.openai_api_key.strip():
            raise LLMError("OPENAI_API_KEY is required when LLM_PROVIDER=openai.")
        return OpenAICompatibleProvider(
            api_key=settings.openai_api_key.strip(),
            base_url=settings.openai_base_url,
            model=settings.openai_model,
            embedding_model=settings.openai_embedding_model,
        )
    raise LLMError(f"Unknown LLM_PROVIDER '{settings.llm_provider}'. Use auto, mock, or openai.")


def resolve_embedding_mode(settings: Settings, provider_name: str) -> str:
    choice = settings.embedding_provider.strip().lower()
    if choice == "local":
        return "local"
    if choice == "openai":
        return "openai"
    if choice == "auto":
        return "local" if provider_name == "mock" else "openai"
    raise LLMError("Unknown EMBEDDING_PROVIDER. Use auto, local, or openai.")


def embed_passages(
    provider: LLMProvider,
    settings: Settings,
    texts: list[str],
) -> tuple[str, list[list[float]]]:
    """Return the embedding space name and one vector per text.

    Remote embeddings fall back to the local hasher when the mode is `auto`,
    so a chat-only host such as Groq still stores searchable chunks.
    """
    if not texts:
        return "local", []
    mode = resolve_embedding_mode(settings, provider.name)
    if mode == "local":
        return "local", local_embed(texts)
    try:
        return "openai", provider.embed_remote(texts)
    except LLMError:
        if settings.embedding_provider.strip().lower() == "openai":
            raise
        logger.warning("Remote embeddings failed; storing local embeddings instead")
        return "local", local_embed(texts)


def embed_query(provider: LLMProvider, mode: str, text: str) -> list[float]:
    if mode == "local":
        return local_embed([text])[0]
    vectors = provider.embed_remote([text])
    return vectors[0]


def summarize_document(provider: LLMProvider, text: str) -> tuple[str, list[str]]:
    if provider.name == "mock":
        return summarize_extractive(text)
    clipped = text[:12000]
    raw = provider.complete(
        [
            {"role": "system", "content": SUMMARY_SYSTEM},
            {"role": "user", "content": clipped},
        ],
        temperature=0.2,
    )
    try:
        return coerce_summary(parse_json_object(raw))
    except (ValueError, LLMError) as exc:
        raise LLMError("The model did not return a usable summary.") from exc


def answer_question(
    provider: LLMProvider,
    question: str,
    passages: list[tuple[int, int, str, float]],
    history: list[tuple[str, str]] | None = None,
) -> str:
    """Passages are (label, chunk_index, text, score)."""
    if provider.name == "mock":
        return answer_extractive(question, passages)
    blocks = []
    for label, _index, text, score in passages:
        blocks.append(f"[{label}] (match {score:.2f})\n{text[:1200]}")
    prior = [
        {"role": role, "content": content}
        for role, content in (history or [])
        if role in {"user", "assistant"}
    ][-6:]
    user = f"Question: {question}\n\nPassages:\n\n" + "\n\n".join(blocks)
    answer = provider.complete(
        [{"role": "system", "content": ANSWER_SYSTEM}, *prior, {"role": "user", "content": user}],
        temperature=0.2,
    ).strip()
    if not answer:
        raise LLMError("The model returned an empty answer.")
    return answer


def summarize_extractive(text: str) -> tuple[str, list[str]]:
    sentences = split_sentences(text)
    if not sentences:
        snippet = text.strip()[:400]
        return snippet, [snippet] if snippet else []
    ranked: list[tuple[float, int, str]] = []
    for index, sentence in enumerate(sentences):
        words = tokenize(sentence)
        if len(words) < 4:
            continue
        score = float(min(len(words), 28) + len(set(words)))
        ranked.append((score, index, sentence))
    ranked.sort(key=lambda item: (-item[0], item[1]))
    chosen = sorted(ranked[:5], key=lambda item: item[1])
    points = [sentence for _score, _index, sentence in chosen] or sentences[:3]
    lead = [sentence for sentence in sentences if len(tokenize(sentence)) >= 4] or sentences
    summary = " ".join(lead[:3])
    if len(summary) < 40:
        summary = " ".join(points[:3])
    return summary[:4000], [point[:400] for point in points[:6]]


def answer_extractive(question: str, passages: list[tuple[int, int, str, float]]) -> str:
    question_tokens = set(tokenize(question))
    ranked: list[tuple[int, float, bool, int, str]] = []
    for label, _index, text, score in passages:
        for sentence in split_sentences(text):
            overlap = len(question_tokens & set(tokenize(sentence)))
            finished = sentence.rstrip().endswith((".", "!", "?"))
            ranked.append((overlap, score, finished, label, sentence))
    ranked.sort(key=lambda item: (item[0], item[1], item[2]), reverse=True)
    picked: list[tuple[int, float, bool, int, str]] = []
    for item in ranked:
        if item[0] <= 0:
            continue
        if any(_same_claim(item[4], earlier[4]) for earlier in picked):
            continue
        picked.append(item)
        if len(picked) == 2:
            break
    if not picked:
        return (
            "I couldn't find that in this document. "
            "The closest passages are cited below, and they do not state a direct answer."
        )
    lines = [f"{sentence} [{label}]" for _overlap, _score, _done, label, sentence in picked]
    return " ".join(lines)


def _same_claim(left: str, right: str) -> bool:
    """True when two sentences are the same claim, including a cut-off copy."""
    normalized = [
        " ".join(sentence.split()).lower().rstrip(".!?") for sentence in (left, right)
    ]
    shorter, longer = sorted(normalized, key=len)
    if not shorter:
        return False
    if shorter == longer:
        return True
    prefix_len = max(24, int(len(shorter) * 0.75))
    return longer.startswith(shorter[:prefix_len])


def parse_json_object(raw: str) -> dict:
    text = raw.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text)
        text = re.sub(r"\s*```$", "", text)
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", text, flags=re.DOTALL)
        if not match:
            raise ValueError("Model did not return JSON")
        data = json.loads(match.group(0))
    if not isinstance(data, dict):
        raise ValueError("Expected a JSON object")
    return data


def coerce_summary(data: dict) -> tuple[str, list[str]]:
    summary = str(data.get("summary") or "").strip()
    raw_points = data.get("key_points")
    if raw_points is None:
        raw_points = data.get("keyPoints") or []
    if isinstance(raw_points, str):
        raw_points = [raw_points]
    if not isinstance(raw_points, list):
        raw_points = []
    points = [str(point).strip()[:400] for point in raw_points if str(point).strip()]
    if not summary and points:
        summary = " ".join(points[:3])
    if not summary:
        raise LLMError("The model returned an empty summary.")
    return summary[:4000], points[:8]
