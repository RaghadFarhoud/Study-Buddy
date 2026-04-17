from __future__ import annotations

from pathlib import Path
from typing import List

from app.domain.models import (
    CanonicalDocument,
    FigureBlock,
    FigureDescriptionBlock,
    BlockType,
)
from app.interpreters.base import Interpreter
from app.services.image_describer import ImageDescriber


class FigureInterpreter(Interpreter):
    def __init__(self, image_describer: ImageDescriber):
        self.image_describer = image_describer

    def interpret(self, document: CanonicalDocument) -> CanonicalDocument:
        for section in document.sections:
            new_blocks = []

            for i, block in enumerate(section.blocks):
                new_blocks.append(block)

                if block.type != BlockType.FIGURE:
                    continue

                figure_block: FigureBlock = block

                if not figure_block.image_path:
                    continue

                context_text = self._build_figure_context(
                    section=section,
                    blocks=section.blocks,
                    figure_index=i,
                    figure_block=figure_block,
                )

                description_text = self.image_describer.describe(
                    image_path=Path(figure_block.image_path),
                    context_text=context_text or None,
                )

                description_text = (description_text or "").strip()
                if not description_text:
                    continue

                desc_block = FigureDescriptionBlock(
                    id=f"{figure_block.id}_desc",
                    order=block.order + 1,
                    page_or_slide=figure_block.page_or_slide,
                    section_path=section.path.copy(),
                    text=description_text,
                    figure_ref_id=figure_block.id,
                    generated_by=self.image_describer.__class__.__name__,
                    metadata={
                        "figure_id": figure_block.id,
                        "generated": True,
                        "context_used": context_text,
                    },
                )

                new_blocks.append(desc_block)

            section.blocks = self._reindex_blocks(new_blocks)

        return document

    def _build_figure_context(self, *, section, blocks, figure_index: int, figure_block: FigureBlock) -> str:
        parts: List[str] = []

        # 1) عنوان القسم
        if section.title:
            parts.append(f"عنوان القسم: {section.title}")

        # 2) كابشن أو alt text إن وجد
        if getattr(figure_block, "caption", None):
            parts.append(f"الكابشن: {figure_block.caption}")

        if getattr(figure_block, "alt_text", None):
            parts.append(f"النص البديل: {figure_block.alt_text}")

        prev_text = self._get_nearby_text(blocks=blocks, start_index=figure_index, direction="backward", max_blocks=2)
        if prev_text:
            section_title_norm = (section.title or "").strip()
            prev_text_norm = prev_text.strip()
            if prev_text_norm != section_title_norm:
                parts.append(f"النص السابق القريب: {prev_text}")

        next_text = self._get_nearby_text(blocks=blocks, start_index=figure_index, direction="forward", max_blocks=2)
        if next_text:
            parts.append(f"النص اللاحق القريب: {next_text}")

        notes = (getattr(section, "notes", None) or "").strip()
        if notes:
            notes = self._truncate_text(notes, max_chars=2500)
            parts.append(f"ملاحظات الشريحة: {notes}")

        return "\n\n".join(part for part in parts if part.strip()).strip()

    def _get_nearby_text(self, *, blocks, start_index: int, direction: str, max_blocks: int = 2) -> str:
        collected: List[str] = []

        if direction == "backward":
            indices = range(start_index - 1, -1, -1)
        else:
            indices = range(start_index + 1, len(blocks))

        for idx in indices:
            if len(collected) >= max_blocks:
                break

            block = blocks[idx]

            # لا نأخذ صورًا أو أوصاف صور أخرى
            if block.type in {BlockType.FIGURE, BlockType.FIGURE_DESCRIPTION}:
                continue

            text = self._block_to_context_text(block)
            if text:
                collected.append(text)

        if direction == "backward":
            collected.reverse()

        return " ".join(collected).strip()

    def _block_to_context_text(self, block) -> str:
        if block.type in {BlockType.PARAGRAPH, BlockType.HEADING, BlockType.CAPTION}:
            return (getattr(block, "text", "") or "").strip()

        if block.type in {BlockType.BULLET_LIST, BlockType.NUMBERED_LIST}:
            items = getattr(block, "items", None) or []
            parts = []

            for item in items[:4]:
                text = (getattr(item, "text", "") or "").strip()
                if text:
                    parts.append(text)

            return " ".join(parts).strip()

        if block.type == BlockType.TABLE:
            summary = (getattr(block, "summary", "") or "").strip()
            return summary

        return ""

    def _truncate_text(self, text: str, max_chars: int = 1800) -> str:
        text = text.strip()
        if len(text) <= max_chars:
            return text
        return text[:max_chars].rstrip() + "..."

    def _reindex_blocks(self, blocks: List) -> List:
        for idx, block in enumerate(blocks, start=1):
            block.order = idx
        return blocks