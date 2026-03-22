from __future__ import annotations

import os
import re
from html import escape

import httpx

from app.segmenter import chunk_markdown, protect_code_segments, restore_code_segments


class AzureTranslatorClient:
    def __init__(self) -> None:
        self.endpoint = os.getenv("AZURE_TRANSLATOR_ENDPOINT", "https://api.cognitive.microsofttranslator.com").rstrip("/")
        self.key = os.getenv("AZURE_TRANSLATOR_KEY")
        self.region = os.getenv("AZURE_TRANSLATOR_REGION")

    @property
    def configured(self) -> bool:
        return bool(self.key and self.region and self.endpoint)

    def translate_html(self, html_content: str, target_language: str, source_language: str | None = None) -> str:
        if not self.configured:
            raise RuntimeError("Azure Translator nao configurado.")

        params = {"api-version": "3.0", "to": target_language, "textType": "html"}
        if source_language:
            params["from"] = source_language

        headers = {
            "Ocp-Apim-Subscription-Key": self.key,
            "Ocp-Apim-Subscription-Region": self.region,
            "Content-Type": "application/json",
        }
        response = httpx.post(
            f"{self.endpoint}/translate",
            params=params,
            headers=headers,
            json=[{"text": html_content}],
            timeout=30,
        )
        response.raise_for_status()
        data = response.json()
        return data[0]["translations"][0]["text"]


def apply_dynamic_dictionary(text: str, glossary: dict[str, str], preserve_terms: list[str]) -> str:
    html_text = escape(text)
    for term in preserve_terms:
        pattern = re.compile(re.escape(term), re.IGNORECASE)
        html_text = pattern.sub(
            lambda match: f'<mstrans:dictionary translation="{escape(match.group(0))}">{escape(match.group(0))}</mstrans:dictionary>',
            html_text,
        )

    for source, target in sorted(glossary.items(), key=lambda item: len(item[0]), reverse=True):
        pattern = re.compile(re.escape(source), re.IGNORECASE)
        html_text = pattern.sub(
            lambda match: f'<mstrans:dictionary translation="{escape(target)}">{escape(match.group(0))}</mstrans:dictionary>',
            html_text,
        )
    return html_text.replace("\n", "<br/>")


def local_preview_transform(text: str, glossary: dict[str, str], preserve_terms: list[str]) -> str:
    transformed = text
    for term in preserve_terms:
        transformed = re.sub(re.escape(term), term, transformed, flags=re.IGNORECASE)
    for source, target in sorted(glossary.items(), key=lambda item: len(item[0]), reverse=True):
        transformed = re.sub(re.escape(source), target, transformed, flags=re.IGNORECASE)
    return transformed


class TranslationService:
    def __init__(self, client: AzureTranslatorClient | None = None) -> None:
        self.client = client or AzureTranslatorClient()

    def translate_article(
        self,
        content: str,
        target_language: str,
        source_language: str | None = None,
        glossary: dict[str, str] | None = None,
        preserve_terms: list[str] | None = None,
    ) -> tuple[str, str, int, str | None]:
        glossary = glossary or {}
        preserve_terms = preserve_terms or []
        protected_text, placeholders = protect_code_segments(content)
        chunks = chunk_markdown(protected_text)

        translated_chunks: list[str] = []
        warning = None

        if self.client.configured:
            provider = "azure_translator"
            if (glossary or preserve_terms) and not source_language:
                warning = "Azure Translator configurado, mas o glossario pode ter efeito reduzido sem `source_language` explicito."
            for chunk in chunks:
                html_payload = apply_dynamic_dictionary(chunk, glossary, preserve_terms)
                translated_html = self.client.translate_html(
                    html_payload,
                    target_language=target_language,
                    source_language=source_language,
                )
                translated_chunks.append(translated_html.replace("<br/>", "\n"))
        else:
            provider = "local_preview"
            warning = "Azure Translator nao esta configurado. Resultado gerado em modo preview com preservacao de termos e glossario."
            for chunk in chunks:
                translated_chunks.append(local_preview_transform(chunk, glossary, preserve_terms))

        merged = "\n\n".join(translated_chunks)
        restored = restore_code_segments(merged, placeholders)
        return restored, provider, len(chunks), warning
