import json

import httpx
import pytest
from app.config import Settings
from app.services.embeddings import EMBEDDING_DIM
from app.services.llm import (
    LLMError,
    MockProvider,
    OpenAICompatibleProvider,
    answer_question,
    build_provider,
    embed_passages,
    summarize_document,
    summarize_extractive,
)


def _settings(**overrides) -> Settings:
    base = dict(
        database_url="sqlite:///:memory:",
        llm_provider="mock",
        embedding_provider="local",
        openai_api_key="",
        openai_base_url="https://example.test/v1",
        openai_model="demo-model",
        openai_embedding_model="demo-embed",
    )
    base.update(overrides)
    return Settings(**base)


def test_auto_without_a_key_is_the_mock():
    provider = build_provider(_settings(llm_provider="auto", openai_api_key=""))
    assert isinstance(provider, MockProvider)


def test_auto_with_a_key_is_openai_compatible():
    provider = build_provider(_settings(llm_provider="auto", openai_api_key="test-key"))
    assert provider.name == "openai"
    assert provider.model == "demo-model"
    provider.close()


def test_openai_provider_requires_a_key():
    with pytest.raises(LLMError, match="OPENAI_API_KEY"):
        build_provider(_settings(llm_provider="openai", openai_api_key=""))


def test_unknown_provider_is_rejected():
    with pytest.raises(LLMError, match="Unknown LLM_PROVIDER"):
        build_provider(_settings(llm_provider="something-else"))


def test_extractive_summary_is_deterministic_and_grounded():
    text = (
        "The Oslo depot warehouse code is Fjord-1842. "
        "The shipping cutoff at that depot is 16:00 local time on weekdays. "
        "The on-call lead for the Nordic region is Mina Solberg."
    )
    first = summarize_extractive(text)
    second = summarize_extractive(text)
    assert first == second
    summary, points = first
    assert "Fjord-1842" in summary
    assert any("Mina Solberg" in point for point in points)


def test_mock_answer_drops_a_cut_off_copy_of_the_same_sentence():
    full = "The on-call lead for the Nordic region is Mina Solberg."
    cut = "The on-call lead for the Nordic region is Mina"
    passages = [(1, 1, full, 0.9), (2, 0, cut, 0.4)]
    answer = answer_question(
        MockProvider(),
        "Who is the on-call lead for the Nordic region?",
        passages,
    )
    assert answer.count("on-call lead") == 1
    assert "Solberg" in answer
    assert "[1]" in answer


def test_mock_answer_quotes_the_passage_or_admits_it_is_missing():
    passages = [(1, 0, "The Oslo depot warehouse code is Fjord-1842.", 0.8)]
    found = answer_question(MockProvider(), "What is the Oslo depot warehouse code?", passages)
    assert "Fjord-1842" in found
    assert "[1]" in found
    missing = answer_question(MockProvider(), "Who baked the banana bread?", passages)
    assert "couldn't find" in missing.lower()
    assert "Fjord-1842" not in missing


def test_openai_summary_accepts_fenced_json():
    def handler(request: httpx.Request) -> httpx.Response:
        payload = '```json\n{"summary": "Wool ships on Tuesday.", "key_points": ["Cutoff is 16:00"]}\n```'
        return httpx.Response(200, json={"choices": [{"message": {"content": payload}}]})

    client = httpx.Client(transport=httpx.MockTransport(handler), base_url="https://example.test/v1")
    provider = OpenAICompatibleProvider(
        api_key="test",
        base_url="https://example.test/v1",
        model="demo-model",
        embedding_model="demo-embed",
        http_client=client,
    )
    summary, points = summarize_document(provider, "source text that is not sent back")
    assert summary == "Wool ships on Tuesday."
    assert points == ["Cutoff is 16:00"]


def test_openai_embeddings_keep_index_order():
    def handler(request: httpx.Request) -> httpx.Response:
        body = json.loads(request.content)
        rows = [{"index": index, "embedding": [float(index), 0.5]} for index in range(len(body["input"]))]
        rows.reverse()
        return httpx.Response(200, json={"data": rows})

    client = httpx.Client(transport=httpx.MockTransport(handler), base_url="https://example.test/v1")
    provider = OpenAICompatibleProvider(
        api_key="test",
        base_url="https://example.test/v1",
        model="demo-model",
        embedding_model="demo-embed",
        http_client=client,
    )
    mode, vectors = embed_passages(provider, _settings(embedding_provider="openai"), ["one", "two"])
    assert mode == "openai"
    assert vectors == [[0.0, 0.5], [1.0, 0.5]]


def test_auto_embeddings_fall_back_to_local_when_the_host_has_no_embeddings():
    class ChatOnly:
        name = "openai"

        def complete(self, messages, *, temperature: float = 0.2) -> str:
            return "{}"

        def embed_remote(self, texts):
            raise LLMError("404")

    mode, vectors = embed_passages(ChatOnly(), _settings(embedding_provider="auto"), ["hello world"])
    assert mode == "local"
    assert len(vectors) == 1
    assert len(vectors[0]) == EMBEDDING_DIM


def test_explicit_openai_embeddings_do_not_silently_change_space():
    class ChatOnly:
        name = "openai"

        def embed_remote(self, texts):
            raise LLMError("404")

    with pytest.raises(LLMError):
        embed_passages(ChatOnly(), _settings(embedding_provider="openai"), ["hello world"])
