from __future__ import annotations

from app.domain.models import CanonicalDocument
from app.normalizers.base import NormalizationPass


class CleanupPass(NormalizationPass):
    def apply(self, document: CanonicalDocument) -> CanonicalDocument:
        for section in document.sections:
            cleaned_blocks = []

            for block in section.blocks:
                if self._should_keep_block(block):
                    cleaned_blocks.append(block)

            for idx, block in enumerate(cleaned_blocks, start=1):
                block.order = idx

            section.blocks = cleaned_blocks

        return document

    def _should_keep_block(self, block) -> bool:
        if getattr(block, "text", None):
            text = block.text.strip()

            if not text:
                return False

            if self._is_separator(text):
                return False

            if self._is_meaningless_text(text):
                return False

        return True

    def _is_separator(self, text: str) -> bool:
        return len(text) >= 3 and set(text) <= {"-", "=", "_", "*", "~"}

    def _is_meaningless_text(self, text: str) -> bool:
        return text in {".", "-", "_", "•", ":"}