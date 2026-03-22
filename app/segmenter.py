from __future__ import annotations

import re


FENCED_CODE_RE = re.compile(r"```[\s\S]*?```")
INLINE_CODE_RE = re.compile(r"`[^`\n]+`")


def protect_code_segments(text: str) -> tuple[str, dict[str, str]]:
    placeholders: dict[str, str] = {}

    def replace_fenced(match: re.Match[str]) -> str:
        key = f"__CODE_BLOCK_{len(placeholders)}__"
        placeholders[key] = match.group(0)
        return key

    def replace_inline(match: re.Match[str]) -> str:
        key = f"__INLINE_CODE_{len(placeholders)}__"
        placeholders[key] = match.group(0)
        return key

    text = FENCED_CODE_RE.sub(replace_fenced, text)
    text = INLINE_CODE_RE.sub(replace_inline, text)
    return text, placeholders


def restore_code_segments(text: str, placeholders: dict[str, str]) -> str:
    restored = text
    for key, value in placeholders.items():
        restored = restored.replace(key, value)
    return restored


def chunk_markdown(text: str, max_chars: int = 3500) -> list[str]:
    paragraphs = text.split("\n\n")
    chunks: list[str] = []
    current = ""

    for paragraph in paragraphs:
        candidate = paragraph if not current else f"{current}\n\n{paragraph}"
        if len(candidate) <= max_chars:
            current = candidate
            continue

        if current:
            chunks.append(current)
        if len(paragraph) <= max_chars:
            current = paragraph
            continue

        for start in range(0, len(paragraph), max_chars):
            chunks.append(paragraph[start : start + max_chars])
        current = ""

    if current:
        chunks.append(current)
    return chunks or [text]
