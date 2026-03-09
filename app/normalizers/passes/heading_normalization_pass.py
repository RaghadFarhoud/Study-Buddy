from __future__ import annotations

from app.domain.models import CanonicalDocument, BlockType
from app.normalizers.base import NormalizationPass


class HeadingNormalizationPass(NormalizationPass):
    def apply(self, document: CanonicalDocument) -> CanonicalDocument:
        for section in document.sections:
            if not section.blocks:
                continue

            normalized_title = self._normalize_text(section.title)

            cleaned_blocks = []
            heading_removed = False

            for idx, block in enumerate(section.blocks):
                if (
                    not heading_removed
                    and block.type == BlockType.HEADING
                    and self._normalize_text(block.text) == normalized_title
                ):
                    heading_removed = True
                    continue

                cleaned_blocks.append(block)

            for idx, block in enumerate(cleaned_blocks, start=1):
                block.order = idx

            section.blocks = cleaned_blocks

        return document

    def _normalize_text(self, text: str | None) -> str:
        if not text:
            return ""
        return " ".join(text.strip().split()).rstrip(":").strip().lower()