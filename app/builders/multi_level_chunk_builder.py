from __future__ import annotations

import re
from typing import List

from app.domain.models import CanonicalDocument, BlockType
from app.domain.outputs import MultiLevelChunkDocument, MultiLevelChunkItem
from app.builders.proposition_refiner import PropositionRefiner

class MultiLevelChunkBuilder:

    def __init__(self, max_paragraph_chars: int = 1200):
        self.max_paragraph_chars = max_paragraph_chars
        self.proposition_refiner = PropositionRefiner()

    def build(self, document: CanonicalDocument) -> MultiLevelChunkDocument:

        chunks: List[MultiLevelChunkItem] = []
        counter = 1

        for section in document.sections:

            if not section.blocks:
                continue

            section_text, block_ids, block_types = self._build_section_text(section.blocks)

            if section_text.strip():

                chunks.append(
                    self._create_chunk(
                        chunk_id=f"{document.document_id}_chunk_{counter}",
                        level="section",
                        document=document,
                        section_title=section.title,
                        section_path=section.path,
                        text=self._prefix_section(section.title, section_text),
                        block_ids=block_ids,
                        block_types=block_types,
                    )
                )

                counter += 1

            paragraph_groups = self._build_paragraph_groups(section.blocks)

            for group in paragraph_groups:

                text = self._join(group["parts"])
                if text.strip() == section_text.strip():
                    continue

                if not text.strip():
                    continue

                chunks.append(
                    self._create_chunk(
                        chunk_id=f"{document.document_id}_chunk_{counter}",
                        level="paragraph",
                        document=document,
                        section_title=section.title,
                        section_path=section.path,
                        text=self._prefix_section(section.title, text),
                        block_ids=group["block_ids"],
                        block_types=group["block_types"],
                    )
                )

                counter += 1

            propositions = self._build_propositions(section.blocks)

            for prop in propositions:

                chunks.append(
                    self._create_chunk(
                        chunk_id=f"{document.document_id}_chunk_{counter}",
                        level="proposition",
                        document=document,
                        section_title=section.title,
                        section_path=section.path,
                        text=prop["text"],
                        block_ids=prop["block_ids"],
                        block_types=prop["block_types"],
                    )
                )

                counter += 1

        return MultiLevelChunkDocument(
            document_id=document.document_id,
            source_type=document.source_type.value,
            source_file=document.source_file,
            chunks=chunks,
            metadata={
                "chunk_count": len(chunks),
                "levels": ["section", "paragraph", "proposition"]
            }
        )

    def _create_chunk(
        self,
        *,
        chunk_id: str,
        level: str,
        document: CanonicalDocument,
        section_title: str,
        section_path: List[str],
        text: str,
        block_ids: List[str],
        block_types: List[str],
    ) -> MultiLevelChunkItem:

        return MultiLevelChunkItem(
            chunk_id=chunk_id,
            level=level,
            document_id=document.document_id,
            section_title=section_title,
            section_path=section_path.copy(),
            text=text.strip(),
            source_block_ids=block_ids,
            block_types=block_types,
        )

    def _build_section_text(self, blocks):

        parts = []
        ids = []
        types = []

        for block in blocks:

            rendered = self._render_block(block)

            if not rendered:
                continue

            parts.append(rendered)
            ids.append(block.id)
            types.append(block.type.value)

        return self._join(parts), ids, types

    def _build_paragraph_groups(self, blocks):

        groups = []

        current_parts = []
        current_ids = []
        current_types = []

        for block in blocks:

            rendered = self._render_block(block)

            if not rendered:
                continue

            candidate = current_parts + [rendered]
            candidate_text = self._join(candidate)

            if current_parts and len(candidate_text) > self.max_paragraph_chars:

                groups.append({
                    "parts": current_parts,
                    "block_ids": current_ids,
                    "block_types": current_types
                })

                current_parts = [rendered]
                current_ids = [block.id]
                current_types = [block.type.value]

            else:

                current_parts.append(rendered)
                current_ids.append(block.id)
                current_types.append(block.type.value)

        if current_parts:

            groups.append({
                "parts": current_parts,
                "block_ids": current_ids,
                "block_types": current_types
            })

        return groups
    
    def _build_propositions(self, blocks)-> List[dict]:

        propositions: List[dict] = []

        for block in blocks:

            if block.type in {BlockType.BULLET_LIST, BlockType.NUMBERED_LIST}:
                items = getattr(block, "items", None) or []

                for item in items:
                    text = (item.text or "").strip()

                    if not text:
                        continue

                    propositions.append({
                        "text": text,
                        "block_ids": [block.id],
                        "block_types": [block.type.value],
                    })

                continue

              

            if block.type == BlockType.FIGURE_DESCRIPTION :
               text = (getattr(block, "text", "") or "") .strip()
               if text:
                propositions.append({
                    "text": text,
                    "block_ids": [block.id],
                    "block_types": [block.type.value],
                })

                continue
         

            if block.type == BlockType.PARAGRAPH :
                text = (getattr(block, "text", "") or "") .strip()
                if not text:
                    continue
 
                refined_props = self.proposition_refiner.refine(text)

                for prop in refined_props:
                    prop = prop.strip()
                    if not prop:
                        continue

                    propositions.append({
                        "text": prop,
                        "block_ids": [block.id],
                        "block_types": [block.type.value],
                    })

        return propositions
    

    def _render_block(self, block):

        if block.type == BlockType.HEADING:
            return ""

        if block.type == BlockType.PARAGRAPH:
            return getattr(block, "text", "") or ""

        if block.type == BlockType.BULLET_LIST:
            if not getattr(block, "items", None):
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

            for idx, item in enumerate(block.items, start=1):
                indent = "  " * item.level
                lines.append(f"{indent}{idx}.{item.text}")
            return "\n".join(lines)

        if block.type == BlockType.FIGURE_DESCRIPTION:
            return getattr(block, "text", "") or ""

        if block.type == BlockType.TABLE:
            summary = getattr(block, "summary", None)

            if summary:
                return f"ملخص الجدول: {summary}"
            return "يوجد جدول في هذا القسم"

        return getattr(block, "text", "") or ""
     
    def _split_sentences(self, text):

        parts = re.split(r"(?<=[\.\!\؟\?؛])\s+", text)

        return [p.strip() for p in parts if p.strip()]

    def _looks_like_proposition(self, sentence):

        markers = ["يجب", "يمكن", "يسمح", "يُسمح", "يعتمد", "تحتوي", "يرتبط"]

        return any(m in sentence for m in markers)

    def _prefix_section(self, title, text):

        if title and title != "Root":
            return f"{title}\n\n{text}"

        return text

    def _join(self, parts):

        return "\n\n".join([p.strip() for p in parts if p.strip()])