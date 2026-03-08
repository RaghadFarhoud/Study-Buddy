from __future__ import annotations

import re


def clean_text(text: str) -> str:
    text = text.replace("\xa0", " ")
    text = re.sub(r"\s+", " ", text).strip()
    return text


def is_empty(text: str | None) -> bool:
    return not text or not text.strip()


def looks_like_caption(text: str) -> bool:
    if not text:
        return False
    lowered = text.strip().lower()
    return (
        lowered.startswith("figure")
        or lowered.startswith("fig.")
        or lowered.startswith("fig ")
        or lowered.startswith("شكل")
        or lowered.startswith("الشكل")
    )