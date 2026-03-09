from __future__ import annotations

from app.domain.models import CanonicalDocument, BlockType
from app.normalizers.base import NormalizationPass


class DuplicateSuppressionPass(NormalizationPass):
    def apply(self, document: CanonicalDocument) -> CanonicalDocument:
        for section in document.sections:
            if not section.blocks:
                continue

            normalized_title = self._normalize_text(section.title)
            cleaned_blocks = []
            previous_text = None

            for idx, block in enumerate(section.blocks):
                block_text = self._normalize_text(getattr(block, "text", None))

                if self._should_drop_as_title_duplicate(
                    block_type=block.type,
                    block_text=block_text,
                    section_title=normalized_title,
                    is_first_content_block=(len(cleaned_blocks) == 0),
                ):
                    continue

                if block_text and previous_text and block_text == previous_text:
                    continue

                cleaned_blocks.append(block)

                if block_text:
                    previous_text = block_text

            for idx, block in enumerate(cleaned_blocks, start=1):
                block.order = idx

            section.blocks = cleaned_blocks

        return document

    def _should_drop_as_title_duplicate(
        self,
        *,
        block_type,
        block_text: str,
        section_title: str,
        is_first_content_block: bool,
    ) -> bool:
        if not block_text or not section_title:
            return False

        if not is_first_content_block:
            return False

        if block_type != BlockType.PARAGRAPH:
            return False

        return block_text == section_title

    def _normalize_text(self, text: str | None) -> str:
        if not text:
            return ""
        return " ".join(text.strip().split()).rstrip(":").strip().lower()