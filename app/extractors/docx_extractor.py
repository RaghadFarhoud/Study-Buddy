from __future__ import annotations

import os
import uuid
from pathlib import Path
from typing import List, Optional

from docx import Document
from docx.table import Table
from docx.text.paragraph import Paragraph
from docx.oxml.ns import qn

from app.domain.models import (
    CanonicalDocument,
    SourceType,
    Section,
    BaseBlock,
    FigureBlock,
    TableBlock,
    TableCell,
    BlockType,
)
from app.services.document_extractor import DocumentExtractor
from app.utils.text_utils import clean_text, is_empty, looks_like_caption


class DocxExtractor(DocumentExtractor):
    def __init__(self, image_output_dir: str = "output/images"):
        self.image_output_dir = Path(image_output_dir)
        self.image_output_dir.mkdir(parents=True, exist_ok=True)

    def extract(self, file_path: str) -> CanonicalDocument:
        doc = Document(file_path)
        doc_id = Path(file_path).stem

        canonical = CanonicalDocument(
            document_id=doc_id,
            source_type=SourceType.DOCX,
            source_file=file_path,
            title=Path(file_path).stem,
            metadata={"extractor": "DocxExtractor"},
        )

        current_section_path: List[str] = []
        current_section = Section(title="Root", path=[], blocks=[])
        sections: List[Section] = [current_section]

        order = 0
        paragraph_texts = [clean_text(p.text) for p in doc.paragraphs if not is_empty(p.text)]

        for block in self._iter_block_items(doc):
            if isinstance(block, Paragraph):
                text = clean_text(block.text)
                if is_empty(text) and not self._paragraph_has_image(block):
                    continue

                style_name = (block.style.name or "").lower() if block.style else ""

                # Heading detection
                if style_name.startswith("heading"):
                    level = self._extract_heading_level(block.style.name)
                    current_section_path = current_section_path[: level - 1]
                    current_section_path.append(text)

                    current_section = Section(
                        title=text,
                        path=current_section_path.copy(),
                        blocks=[]
                    )
                    sections.append(current_section)

                    order += 1
                    heading_block = BaseBlock(
                        id=self._new_id(),
                        type=BlockType.HEADING,
                        order=order,
                        text=text,
                        section_path=current_section_path.copy(),
                        metadata={"style_name": block.style.name, "heading_level": level},
                    )
                    current_section.blocks.append(heading_block)
                    continue

                # Embedded image inside paragraph
                if self._paragraph_has_image(block):
                    saved_images = self._extract_images_from_paragraph(block, doc_id)
                    caption = self._guess_caption(block)

                    for image_path in saved_images:
                        order += 1
                        fig_block = FigureBlock(
                            id=self._new_id(),
                            type=BlockType.FIGURE,
                            order=order,
                            text=None,
                            image_path=str(image_path),
                            caption=caption,
                            section_path=current_section_path.copy(),
                            metadata={
                                "style_name": block.style.name if block.style else None,
                            },
                        )
                        current_section.blocks.append(fig_block)

                # Paragraph / Bullet
                if not is_empty(text):
                    block_type = (
                        BlockType.BULLET_LIST
                        if self._is_list_paragraph(block)
                        else BlockType.PARAGRAPH
                    )

                    order += 1
                    para_block = BaseBlock(
                        id=self._new_id(),
                        type=block_type,
                        order=order,
                        text=text,
                        section_path=current_section_path.copy(),
                        metadata={
                            "style_name": block.style.name if block.style else None,
                        },
                    )
                    current_section.blocks.append(para_block)

            elif isinstance(block, Table):
                table_block = self._extract_table(block, order + 1, current_section_path)
                order = table_block.order
                current_section.blocks.append(table_block)

        canonical.sections = sections
        return canonical

    def _extract_table(
        self,
        table: Table,
        order: int,
        section_path: List[str],
    ) -> TableBlock:
        cells: List[TableCell] = []
        rows = len(table.rows)
        cols = max((len(r.cells) for r in table.rows), default=0)

        for i, row in enumerate(table.rows):
            for j, cell in enumerate(row.cells):
                text = clean_text(cell.text)
                cells.append(TableCell(row=i, col=j, text=text))

        summary = self._summarize_table(cells, rows, cols)

        return TableBlock(
            id=self._new_id(),
            type=BlockType.TABLE,
            order=order,
            rows=rows,
            cols=cols,
            cells=cells,
            summary=summary,
            section_path=section_path.copy(),
            metadata={},
        )

    def _summarize_table(self, cells: List[TableCell], rows: int, cols: int) -> str:
        if not cells:
            return "جدول فارغ"

        first_row = [c.text for c in cells if c.row == 0]
        headers = [x for x in first_row if x]
        if headers:
            return f"جدول يحتوي على {rows} صفوف و {cols} أعمدة. العناوين المحتملة: {', '.join(headers[:5])}"
        return f"جدول يحتوي على {rows} صفوف و {cols} أعمدة"

    def _is_list_paragraph(self, paragraph: Paragraph) -> bool:
        style_name = (paragraph.style.name or "").lower() if paragraph.style else ""
        return "list" in style_name or "bullet" in style_name

    def _extract_heading_level(self, style_name: str) -> int:
        # Examples: Heading 1, Heading 2
        parts = style_name.strip().split()
        for p in reversed(parts):
            if p.isdigit():
                return int(p)
        return 1

    def _paragraph_has_image(self, paragraph: Paragraph) -> bool:
        # Detect drawing or pict elements inside the paragraph XML
        xml = paragraph._element.xml
        return ("pic:pic" in xml) or ("a:blip" in xml)

    def _guess_caption(self, paragraph: Paragraph) -> Optional[str]:
        text = clean_text(paragraph.text)
        if looks_like_caption(text):
            return text
        return None

    def _extract_images_from_paragraph(self, paragraph: Paragraph, doc_id: str) -> List[Path]:
        image_paths: List[Path] = []
        rel_ids = []

        # Search for embedded image relationships in paragraph XML
        blips = paragraph._element.xpath(".//a:blip")
        for blip in blips:
            embed = blip.get(qn("r:embed"))
            if embed:
                rel_ids.append(embed)

        for rel_id in rel_ids:
            rel = paragraph.part.related_parts.get(rel_id)
            if rel is None:
                continue

            image_bytes = rel.blob
            ext = self._guess_extension(rel.content_type)
            filename = f"{doc_id}_{uuid.uuid4().hex[:8]}.{ext}"
            out_path = self.image_output_dir / filename

            with open(out_path, "wb") as f:
                f.write(image_bytes)

            image_paths.append(out_path)

        return image_paths

    def _guess_extension(self, content_type: str) -> str:
        mapping = {
            "image/png": "png",
            "image/jpeg": "jpg",
            "image/jpg": "jpg",
            "image/gif": "gif",
            "image/bmp": "bmp",
            "image/tiff": "tiff",
        }
        return mapping.get(content_type, "bin")

    def _iter_block_items(self, parent):
        """
        Iterate over paragraphs and tables in document order.
        """
        from docx.document import Document as _Document
        from docx.oxml.table import CT_Tbl
        from docx.oxml.text.paragraph import CT_P
        from docx.table import _Cell, Table
        from docx.text.paragraph import Paragraph

        if isinstance(parent, _Document):
            parent_elm = parent.element.body
        elif isinstance(parent, _Cell):
            parent_elm = parent._tc
        else:
            raise ValueError("Unsupported parent type")

        for child in parent_elm.iterchildren():
            if isinstance(child, CT_P):
                yield Paragraph(child, parent)
            elif isinstance(child, CT_Tbl):
                yield Table(child, parent)

    def _new_id(self) -> str:
        return uuid.uuid4().hex