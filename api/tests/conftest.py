import pytest
from fastapi.testclient import TestClient


@pytest.fixture(autouse=True)
def isolated_provider(monkeypatch):
    """Keep the suite on the mock provider even if a developer has a local .env."""
    monkeypatch.setenv("LLM_PROVIDER", "mock")
    monkeypatch.setenv("EMBEDDING_PROVIDER", "local")
    monkeypatch.setenv("OPENAI_API_KEY", "")
    from app.config import get_settings

    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{tmp_path / 'test.db'}")
    monkeypatch.setenv("LLM_PROVIDER", "mock")
    monkeypatch.setenv("EMBEDDING_PROVIDER", "local")
    monkeypatch.setenv("OPENAI_API_KEY", "")
    from app.config import get_settings
    from app.main import create_app

    get_settings.cache_clear()
    application = create_app()
    with TestClient(application) as test_client:
        yield test_client
    get_settings.cache_clear()
