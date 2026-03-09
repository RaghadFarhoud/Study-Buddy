from __future__ import annotations

import re
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
from app.utils.text_utils import (
    clean_text,
    looks_like_caption,
    looks_like_numbered_item,
    is_meaningful_text,
    looks_like_heading_by_text,
)


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
        blocks = list(self._iter_block_items(doc))

        for idx, block in enumerate(blocks):
            if isinstance(block, Paragraph):
                text = clean_text(block.text)

                if not is_meaningful_text(text) and not self._paragraph_has_image(block):
                    continue

                is_heading = (
                    self._is_heading_paragraph(block, text)
                    or self._is_intro_heading_before_list(blocks, idx, text)
                )

                if is_heading and is_meaningful_text(text):
                    level = self._resolve_heading_level(block, text)
                    current_section_path = current_section_path[: level - 1]
                    current_section_path.append(text)

                    current_section = Section(
                        title=text,
                        path=current_section_path.copy(),
                        blocks=[],
                    )
                    sections.append(current_section)

                    order += 1
                    heading_block = BaseBlock(
                        id=self._new_id(),
                        type=BlockType.HEADING,
                        order=order,
                        text=text,
                        section_path=current_section_path.copy(),
                        metadata={
                            "style_name": block.style.name if block.style else None,
                            "heading_level": level,
                            "heading_source": self._heading_source(block, text, blocks, idx),
                        },
                    )
                    current_section.blocks.append(heading_block)
                    continue

                if self._paragraph_has_image(block):
                    saved_images = self._extract_images_from_paragraph(block, doc_id)
                    caption = self._guess_caption(block)
                    alt_text = self._extract_alt_text(block)

                    for image_path in saved_images:
                        order += 1
                        fig_block = FigureBlock(
                            id=self._new_id(),
                            type=BlockType.FIGURE,
                            order=order,
                            text=None,
                            image_path=str(image_path),
                            image_name=Path(image_path).name,
                            caption=caption,
                            rel_id=None,
                            alt_text=alt_text,
                            section_path=current_section_path.copy(),
                            metadata={
                                "style_name": block.style.name if block.style else None,
                            },
                        )
                        current_section.blocks.append(fig_block)

                if is_meaningful_text(text):
                    block_type = self._classify_paragraph_type(block, text)

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

    def _classify_paragraph_type(self, paragraph: Paragraph, text: str) -> BlockType:
        style_name = (paragraph.style.name or "").lower() if paragraph.style else ""

        if looks_like_caption(text):
            return BlockType.CAPTION

        if looks_like_numbered_item(text):
            return BlockType.NUMBERED_LIST

        if "list" in style_name or "bullet" in style_name:
            return BlockType.BULLET_LIST

        return BlockType.PARAGRAPH

    def _is_heading_paragraph(self, paragraph: Paragraph, text: str) -> bool:
        style_name = (paragraph.style.name or "").lower() if paragraph.style else ""

    # الحالة 1: heading style
        if style_name.startswith("heading"):
            return True

        text = clean_text(text)
        if not text:
            return False

    # الحالة 2: intro before list
    # مثال:
    # المتطلبات الأمنية:
    # 1) ...
        if text.endswith(":"):
            return True

    # الحالة 3: headings مرقمة
    # مثل:
    # 1 Introduction
    # 1.2 Architecture
        if re.match(r"^\d+(\.\d+)*\s+.+$", text):
            return True

    # الحالة 4: عناوين عربية شائعة
        heading_keywords = [
            "المطلوب",
            "المقدمة",
             "الخاتمة",
             "النتائج",
             "التوصيات",
        ]

        normalized = text.strip().rstrip(":")
        if normalized in heading_keywords:
            return True

        return False

    def _resolve_heading_level(self, paragraph: Paragraph, text: str) -> int:
        style_name = paragraph.style.name if paragraph.style else ""

        if style_name and style_name.lower().startswith("heading"):
            return self._extract_heading_level(style_name)

        text = clean_text(text)

        match = re.match(r"^(\d+(?:\.\d+)*)\s+.+$", text)
        if match:
            return match.group(1).count(".") + 1

        match_ar = re.match(r"^([٠-٩]+(?:\.\d+)*)\s+.+$", text)
        if match_ar:
            return match_ar.group(1).count(".") + 1

        if text.endswith(":"):
            return 1

        return 1

    def _heading_source(
        self,
        paragraph: Paragraph,
        text: str,
        blocks=None,
        index: int | None = None,
    ) -> str:
        style_name = (paragraph.style.name or "").lower() if paragraph.style else ""

        if style_name.startswith("heading"):
            return "style"

        if looks_like_heading_by_text(text):
            return "heuristic"

        if blocks is not None and index is not None and self._is_intro_heading_before_list(blocks, index, text):
            return "intro_before_list"

        return "unknown"

    def _is_intro_heading_before_list(self, blocks, index: int, text: str) -> bool:
        text = clean_text(text)
        if not text:
            return False

        if not text.endswith(":"):
            return False

        look_ahead_limit = 2
        for offset in range(1, look_ahead_limit + 1):
            next_index = index + offset
            if next_index >= len(blocks):
                break

            next_block = blocks[next_index]

            if isinstance(next_block, Paragraph):
                next_text = clean_text(next_block.text)

                if looks_like_numbered_item(next_text):
                    return True

                style_name = (next_block.style.name or "").lower() if next_block.style else ""
                if "list" in style_name or "bullet" in style_name:
                    return True

        return False

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

    def _extract_heading_level(self, style_name: str) -> int:
        parts = style_name.strip().split()
        for p in reversed(parts):
            if p.isdigit():
                return int(p)
        return 1

    def _paragraph_has_image(self, paragraph: Paragraph) -> bool:
        xml = paragraph._element.xml
        return ("pic:pic" in xml) or ("a:blip" in xml)

    def _guess_caption(self, paragraph: Paragraph) -> Optional[str]:
        text = clean_text(paragraph.text)
        if looks_like_caption(text):
            return text
        return None

    def _extract_alt_text(self, paragraph: Paragraph) -> Optional[str]:
        try:
            doc_pr = paragraph._element.xpath(".//wp:docPr")
            if not doc_pr:
                return None

            descr = doc_pr[0].get("descr")
            if descr:
                return clean_text(descr)

            title = doc_pr[0].get("title")
            if title:
                return clean_text(title)

            return None
        except Exception:
            return None

    def _extract_images_from_paragraph(self, paragraph: Paragraph, doc_id: str) -> List[Path]:
        image_paths: List[Path] = []
        rel_ids = []

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
            "image/webp": "webp",
        }
        return mapping.get(content_type, "bin")

    def _iter_block_items(self, parent):
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