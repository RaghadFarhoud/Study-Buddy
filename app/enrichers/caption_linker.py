from __future__ import annotations

from app.domain.models import CanonicalDocument, FigureBlock
from app.domain.models import BlockType


class CaptionLinker:
    def link(self, document: CanonicalDocument) -> CanonicalDocument:
        for section in document.sections:
            blocks = section.blocks

            for idx, block in enumerate(blocks):
                if block.type != BlockType.FIGURE or not isinstance(block, FigureBlock):
                    continue

                caption = self._find_nearest_caption(blocks, idx)
                if caption:
                    block.caption = caption

        return document

    def _find_nearest_caption(self, blocks, index: int) -> str | None:
        # نفحص قبله ثم بعده ضمن نافذة صغيرة
        for offset in range(1, 3):
            prev_idx = index - offset
            if prev_idx >= 0:
                prev_block = blocks[prev_idx]
                if prev_block.type == BlockType.CAPTION and prev_block.text:
                    return prev_block.text

            next_idx = index + offset
            if next_idx < len(blocks):
                next_block = blocks[next_idx]
                if next_block.type == BlockType.CAPTION and next_block.text:
                    return next_block.text

        return None