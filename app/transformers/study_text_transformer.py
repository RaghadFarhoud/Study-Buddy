from __future__ import annotations

from typing import List

from app.domain.models import CanonicalDocument, FigureBlock, TableBlock, BaseBlock
from app.domain.views import StudyTextView, StudyTextSection
from app.domain.models import BlockType


class StudyTextTransformer:
    def transform(self, document: CanonicalDocument) -> StudyTextView:
        rendered_sections: List[StudyTextSection] = []

        for section in document.sections:
            if not section.blocks:
                continue

            rendered_text = self._render_section(section.blocks)

            if not rendered_text.strip():
                continue

            rendered_sections.append(
                StudyTextSection(
                    title=section.title if section.title != "Root" else None,
                    section_path=section.path,
                    text=rendered_text,
                    metadata={},
                )
            )

        full_text = self._join_sections(rendered_sections)

        return StudyTextView(
            document_id=document.document_id,
            title=document.title,
            full_text=full_text,
            sections=rendered_sections,
            metadata={
                "source_type": document.source_type.value,
                "source_file": document.source_file,
            },
        )

    def _render_section(self, blocks: List[BaseBlock]) -> str:
        lines: List[str] = []

        for block in blocks:
            if block.type == BlockType.HEADING:
                if block.text:
                    lines.append(block.text)
                    lines.append("")

            elif block.type == BlockType.PARAGRAPH:
                if block.text:
                    lines.append(block.text)
                    lines.append("")

            elif block.type == BlockType.BULLET_LIST:
                if block.text:
                    lines.append(f"- {block.text}")
                    lines.append("")

            elif block.type == BlockType.NUMBERED_LIST:
                if block.text:
                    lines.append(block.text)
                    lines.append("")

            elif block.type == BlockType.CAPTION:
                if block.text:
                    lines.append(f"توضيح الشكل: {block.text}")
                    lines.append("")

            elif block.type == BlockType.FIGURE:
                if isinstance(block, FigureBlock):
                    figure_lines = []

                    if block.caption:
                        figure_lines.append(f"عنوان الشكل: {block.caption}")

                    if block.alt_text:
                        figure_lines.append(f"النص البديل للصورة: {block.alt_text}")

                    if figure_lines:
                        lines.extend(figure_lines)
                        lines.append("")

            elif block.type == BlockType.FIGURE_DESCRIPTION:
                if block.text:
                    lines.append(f"شرح الصورة: {block.text}")
                    lines.append("")

            elif block.type == BlockType.TABLE:
                if isinstance(block, TableBlock):
                    if block.summary:
                        lines.append(f"ملخص الجدول: {block.summary}")
                        lines.append("")
                    else:
                        lines.append("يوجد جدول في هذا القسم.")
                        lines.append("")

        return self._normalize_rendered_text(lines)

    def _join_sections(self, sections: List[StudyTextSection]) -> str:
        parts: List[str] = []

        for section in sections:
            if section.title:
                parts.append(section.title)
                parts.append("")

            parts.append(section.text.strip())
            parts.append("")

        return "\n".join(part for part in parts if part is not None).strip()

    def _normalize_rendered_text(self, lines: List[str]) -> str:
        text = "\n".join(lines)

        while "\n\n\n" in text:
            text = text.replace("\n\n\n", "\n\n")

        return text.strip()