from __future__ import annotations

from typing import List

from app.domain.models import CanonicalDocument, FigureBlock, TableBlock
from app.domain.models import BlockType
from app.domain.views import RagChunk, RagChunkView


class RagChunkTransformer:
    def __init__(self, max_chars: int = 1200):
        self.max_chars = max_chars

    def transform(self, document: CanonicalDocument) -> RagChunkView:
        chunks: List[RagChunk] = []
        chunk_counter = 1

        for section in document.sections:
            if not section.blocks:
                continue

            current_text_parts: List[str] = []
            current_block_ids: List[str] = []
            current_has_figure = False
            current_has_table = False

            section_title = section.title if section.title != "Root" else None

            for block in section.blocks:
                rendered = self._render_block_for_rag(block)
                if not rendered:
                    continue

                candidate_text = self._join_parts(current_text_parts + [rendered])

                if current_text_parts and len(candidate_text) > self.max_chars:
                    chunks.append(
                        self._build_chunk(
                            document=document,
                            chunk_id=f"{document.document_id}_{chunk_counter}",
                            chunk_type=self._infer_chunk_type(
                                has_figure=current_has_figure,
                                has_table=current_has_table,
                            ),
                            text=self._finalize_chunk_text(
                                section_title=section_title,
                                text=self._join_parts(current_text_parts),
                            ),
                            section_path=section.path,
                            block_ids=current_block_ids,
                            has_figure=current_has_figure,
                            has_table=current_has_table,
                        )
                    )
                    chunk_counter += 1

                    current_text_parts = [rendered]
                    current_block_ids = [block.id]
                    current_has_figure = block.type == BlockType.FIGURE or block.type == BlockType.FIGURE_DESCRIPTION
                    current_has_table = block.type == BlockType.TABLE
                else:
                    current_text_parts.append(rendered)
                    current_block_ids.append(block.id)

                    if block.type in {BlockType.FIGURE, BlockType.FIGURE_DESCRIPTION}:
                        current_has_figure = True

                    if block.type == BlockType.TABLE:
                        current_has_table = True

            if current_text_parts:
                chunks.append(
                    self._build_chunk(
                        document=document,
                        chunk_id=f"{document.document_id}_{chunk_counter}",
                        chunk_type=self._infer_chunk_type(
                            has_figure=current_has_figure,
                            has_table=current_has_table,
                        ),
                        text=self._finalize_chunk_text(
                            section_title=section_title,
                            text=self._join_parts(current_text_parts),
                        ),
                        section_path=section.path,
                        block_ids=current_block_ids,
                        has_figure=current_has_figure,
                        has_table=current_has_table,
                    )
                )
                chunk_counter += 1

        return RagChunkView(
            document_id=document.document_id,
            chunks=chunks,
            metadata={
                "source_type": document.source_type.value,
                "source_file": document.source_file,
                "chunk_count": len(chunks),
            },
        )

    def _render_block_for_rag(self, block) -> str:
        if block.type == BlockType.HEADING and block.text:
            return f"العنوان: {block.text}"

        if block.type == BlockType.PARAGRAPH and block.text:
            return block.text

        if block.type == BlockType.BULLET_LIST and block.text:
            return f"نقطة: {block.text}"

        if block.type == BlockType.NUMBERED_LIST and block.text:
            return f"متطلب: {block.text}"

        if block.type == BlockType.CAPTION and block.text:
            return f"توضيح الشكل: {block.text}"

        if block.type == BlockType.FIGURE and isinstance(block, FigureBlock):
            parts: List[str] = []

            if block.caption:
                parts.append(f"عنوان الشكل: {block.caption}")

            if block.alt_text:
                parts.append(f"النص البديل للصورة: {block.alt_text}")

            return "\n".join(parts).strip()

        if block.type == BlockType.FIGURE_DESCRIPTION and block.text:
            return f"شرح الصورة: {block.text}"

        if block.type == BlockType.TABLE and isinstance(block, TableBlock):
            if block.summary:
                return f"ملخص الجدول: {block.summary}"
            return "يوجد جدول في هذا القسم."

        return ""

    def _build_chunk(
        self,
        *,
        document: CanonicalDocument,
        chunk_id: str,
        chunk_type: str,
        text: str,
        section_path: List[str],
        block_ids: List[str],
        has_figure: bool,
        has_table: bool,
    ) -> RagChunk:
        return RagChunk(
            chunk_id=chunk_id,
            document_id=document.document_id,
            chunk_type=chunk_type,
            text=text,
            section_path=section_path,
            source_file=document.source_file,
            block_ids=block_ids,
            has_figure=has_figure,
            has_table=has_table,
            metadata={
                "source_type": document.source_type.value,
            },
        )

    def _infer_chunk_type(self, *, has_figure: bool, has_table: bool) -> str:
        if has_figure and has_table:
            return "section_with_figure_and_table"
        if has_figure:
            return "section_with_figure"
        if has_table:
            return "section_with_table"
        return "section_text"

    def _finalize_chunk_text(self, *, section_title: str | None, text: str) -> str:
        parts: List[str] = []

        if section_title:
            parts.append(f"القسم: {section_title}")

        parts.append(text.strip())

        return "\n\n".join(p for p in parts if p.strip())

    def _join_parts(self, parts: List[str]) -> str:
        return "\n\n".join(p.strip() for p in parts if p and p.strip()).strip()