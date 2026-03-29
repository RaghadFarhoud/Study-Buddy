from __future__ import annotations

import re
from collections import Counter
from typing import List

from app.domain.models import CanonicalDocument, Section, BaseBlock, BlockType


class RepeatedPageNoisePass:
    def apply(self, document: CanonicalDocument) -> CanonicalDocument:
        repeated_noise = self._detect_repeated_noise(document)
        cleaned_sections: List[Section] = []

        for section in document.sections:
            kept_blocks: List[BaseBlock] = []

            for block in section.blocks:
                text = self._normalize(block.text)

                if block.type == BlockType.PARAGRAPH:
                    if self._is_page_number(text):
                        continue

                    if text in repeated_noise:
                        continue

                    if self._is_safe_footer_noise(text):
                        continue

                kept_blocks.append(block)

            cleaned_sections.append(
                Section(
                    title=section.title,
                    path=section.path.copy(),
                    blocks=self._reindex(kept_blocks),
                )
            )

        document.sections = cleaned_sections
        return document

    def _detect_repeated_noise(self, document: CanonicalDocument) -> set[str]:
        texts: List[str] = []

        for section in document.sections:
            for block in section.blocks:
                if block.type != BlockType.PARAGRAPH:
                    continue

                text = self._normalize(block.text)
                if not text:
                    continue

                if len(text) <= 60:
                    texts.append(text)

        counts = Counter(texts)

        return {
            text for text, count in counts.items()
            if count >= 2 and self._looks_like_repeated_header_footer(text)
        }

    def _looks_like_repeated_header_footer(self, text: str) -> bool:
        patterns = [
            r"/[A-Za-z0-9\.\-_]+",
            r"ITE\.RBCs",
            r"بيانيات حاسوبية\|",
            r"د\.",
        ]
        return any(re.search(p, text) for p in patterns)

    def _is_page_number(self, text: str) -> bool:
        return bool(
            re.fullmatch(r"\d{1,3}", text)
            or re.fullmatch(r"\d{1,3}\s*/\s*\d{1,3}", text)
        )

    def _is_safe_footer_noise(self, text: str) -> bool:
        if not text:
            return False

        if re.fullmatch(r"/[A-Za-z0-9\.\-_]+", text):
            return True

        return False

    def _normalize(self, text: str | None) -> str:
        if not text:
            return ""
        return re.sub(r"\s+", " ", text).strip()

    def _reindex(self, blocks: List[BaseBlock]) -> List[BaseBlock]:
        for idx, block in enumerate(blocks, start=1):
            block.order = idx
        return blocks