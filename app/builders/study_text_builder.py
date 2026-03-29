from __future__ import annotations

from typing import List

from app.domain.models import CanonicalDocument, BlockType
from app.domain.outputs import StudyTextDocument, StudyTextSection


class StudyTextBuilder:

    def build(self, document: CanonicalDocument) -> StudyTextDocument:
        built_sections: List[StudyTextSection] = []

        for section in document.sections:
            if not section.blocks:
                continue

            section_text = self._render_section(section.title, section.blocks)

            if not section_text.strip():
                continue

            built_sections.append(
                StudyTextSection(
                    title=section.title,
                    section_path=section.path.copy(),
                    text=section_text,
                    metadata={},
                )
            )

        full_text = self._join_sections(built_sections)

        return StudyTextDocument(
            document_id=document.document_id,
            source_type=document.source_type.value,
            source_file=document.source_file,
            title=document.title,
            full_text=full_text,
            sections=built_sections,
            metadata={
                "section_count": len(built_sections)
            },
        )

    def _render_section(self, title: str | None, blocks) -> str:
        parts: List[str] = []

        if title and title != "Root":
            parts.append(title)
            parts.append("")

        for block in blocks:
            rendered = self._render_block(block)

            if rendered:
                parts.append(rendered)
                parts.append("")

        return self._cleanup_text("\n".join(parts))

    def _render_block(self, block) -> str:

        if block.type == BlockType.HEADING:
            return ""

        if block.type == BlockType.PARAGRAPH:
            return block.text or ""

        if block.type == BlockType.BULLET_LIST:
            if not block.items:
                return ""
            
            lines = []

            for item in block.items:
                indent = "  " * item.level
                lines.append(f"{indent}- {item.text}") 
            return "\n".join(lines)

        if block.type == BlockType.NUMBERED_LIST:
           if not getattr(block, "items", None):
                return ""
            
           lines = []

           for idx, item in enumerate(block.items, start=1 ):
                indent = "  " * item.level
                lines.append(f"{indent}{idx}.{item.text}") 
           return "\n".join(lines)

        if block.type == BlockType.CAPTION:
            text = getattr(block, "text", "") or ""

            if text:
                return f"توضيح الشكل: {block.text}"
            return ""

        if block.type == BlockType.FIGURE:
            return ""

        if block.type == BlockType.FIGURE_DESCRIPTION:
            return getattr(block, "text", "") or ""

        if block.type == BlockType.TABLE:
            summary = getattr(block, "summary", None)

            if summary:
                return f"ملخص الجدول: {summary}"

            return "يوجد جدول في هذا القسم."

        return getattr(block, "text", "") or ""

    def _join_sections(self, sections: List[StudyTextSection]) -> str:
        parts: List[str] = []

        for section in sections:
            if section.text.strip():
                parts.append(section.text.strip())

        return self._cleanup_text("\n\n".join(parts))

    def _cleanup_text(self, text: str) -> str:
        while "\n\n\n" in text:
            text = text.replace("\n\n\n", "\n\n")

        return text.strip()