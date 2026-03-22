from pydantic import BaseModel, Field


class TranslateArticleRequest(BaseModel):
    content: str = Field(min_length=1, description="Conteudo do artigo em texto puro ou markdown")
    target_language: str = Field(default="pt-br", description="Idioma de destino")
    source_language: str | None = Field(default=None, description="Idioma de origem opcional")
    glossary: dict[str, str] = Field(default_factory=dict, description="Termos tecnicos para preservar ou customizar")
    preserve_terms: list[str] = Field(default_factory=list, description="Termos que nao devem ser traduzidos")
    title: str | None = None


class TranslateArticleResponse(BaseModel):
    title: str | None
    source_language: str | None
    target_language: str
    provider: str
    translated_content: str
    preserved_terms: list[str]
    applied_glossary: dict[str, str]
    chunks_processed: int
    warning: str | None = None
