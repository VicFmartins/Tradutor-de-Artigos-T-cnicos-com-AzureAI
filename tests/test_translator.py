from fastapi.testclient import TestClient

from app.main import app
from app.segmenter import chunk_markdown, protect_code_segments, restore_code_segments
from app.translator import TranslationService


client = TestClient(app)


SAMPLE_ARTICLE = """# Deploying a FastAPI Service

The service exposes an endpoint for authentication and cache invalidation.

```python
def authenticate_user(token: str) -> bool:
    return token.startswith("Bearer ")
```

Use `docker compose up` to start the environment.
"""


def test_code_protection_and_restore() -> None:
    protected, placeholders = protect_code_segments(SAMPLE_ARTICLE)
    assert "authenticate_user" not in protected
    restored = restore_code_segments(protected, placeholders)
    assert restored == SAMPLE_ARTICLE


def test_chunk_markdown_returns_non_empty_chunks() -> None:
    chunks = chunk_markdown(SAMPLE_ARTICLE, max_chars=80)
    assert len(chunks) >= 2
    assert all(chunks)


def test_local_preview_applies_glossary_and_preserves_code() -> None:
    service = TranslationService()
    translated, provider, chunks_processed, warning = service.translate_article(
        content=SAMPLE_ARTICLE,
        target_language="pt-br",
        glossary={"authentication": "autenticacao", "cache invalidation": "invalidacao de cache"},
        preserve_terms=["FastAPI", "docker compose up"],
    )

    assert provider == "local_preview"
    assert chunks_processed >= 1
    assert warning is not None
    assert "autenticacao" in translated
    assert "invalidacao de cache" in translated
    assert "FastAPI" in translated
    assert "`docker compose up`" in translated
    assert "def authenticate_user" in translated


def test_api_returns_translation_payload() -> None:
    response = client.post(
        "/api/translate/article",
        json={
            "title": "Deploying a FastAPI Service",
            "content": SAMPLE_ARTICLE,
            "target_language": "pt-br",
            "glossary": {
                "authentication": "autenticacao",
                "cache invalidation": "invalidacao de cache"
            },
            "preserve_terms": ["FastAPI", "docker compose up"]
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["provider"] in {"local_preview", "azure_translator"}
    assert data["target_language"] == "pt-br"
    assert "FastAPI" in data["translated_content"]
