from fastapi import FastAPI

from app.models import TranslateArticleRequest, TranslateArticleResponse
from app.translator import TranslationService


app = FastAPI(
    title="Tradutor Tecnico com Azure AI",
    version="1.0.0",
    description="API para traducao de artigos tecnicos com preservacao de codigo, glossario e integracao opcional com Azure Translator.",
)

service = TranslationService()


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "tradutor-azureai"}


@app.post("/api/translate/article", response_model=TranslateArticleResponse)
def translate_article(payload: TranslateArticleRequest) -> TranslateArticleResponse:
    translated_content, provider, chunks_processed, warning = service.translate_article(
        content=payload.content,
        target_language=payload.target_language,
        source_language=payload.source_language,
        glossary=payload.glossary,
        preserve_terms=payload.preserve_terms,
    )
    return TranslateArticleResponse(
        title=payload.title,
        source_language=payload.source_language,
        target_language=payload.target_language,
        provider=provider,
        translated_content=translated_content,
        preserved_terms=payload.preserve_terms,
        applied_glossary=payload.glossary,
        chunks_processed=chunks_processed,
        warning=warning,
    )
