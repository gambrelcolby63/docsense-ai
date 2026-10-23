from app.database import database_kind, make_engine, normalize_database_url


def test_render_style_postgres_url_uses_psycopg():
    raw = "postgres://docsense:secret@localhost:5432/docsense"
    normalized = normalize_database_url(raw)
    assert normalized.startswith("postgresql+psycopg://")
    engine = make_engine(raw)
    assert engine.dialect.name == "postgresql"
    assert engine.url.drivername == "postgresql+psycopg"
    assert database_kind(raw) == "postgres"


def test_plain_postgresql_url_is_normalized():
    url = "postgresql://docsense:secret@localhost:5432/docsense"
    assert normalize_database_url(url).startswith("postgresql+psycopg://")


def test_sqlite_memory_engine():
    engine = make_engine("sqlite:///:memory:")
    assert engine.dialect.name == "sqlite"
    assert database_kind("sqlite:///./data/docsense.db") == "sqlite"
