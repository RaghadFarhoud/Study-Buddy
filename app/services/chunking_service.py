from __future__ import annotations

from pydantic import BaseModel, Field
from typing import List, Dict, Any

from app.domain.models import CanonicalDocument, FigureBlock, TableBlock
from app.domain.models import BlockType


class Chunk(BaseModel):
    chunk_id: str
    text: str
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ChunkingService:
    def build_chunks(self, document: CanonicalDocument) -> List[Chunk]:
        chunks: List[Chunk] = []

        for section in document.sections:
            current_texts = []
            current_metadata = {
                "document_id": document.document_id,
                "source_file": document.source_file,
                "section_path": section.path,
            }

            for block in section.blocks:
                if block.type in {BlockType.HEADING, BlockType.PARAGRAPH, BlockType.BULLET_LIST, BlockType.NUMBERED_LIST, BlockType.CAPTION, BlockType.FIGURE_DESCRIPTION}:
                    if block.text:
                        current_texts.append(block.text)

                elif block.type == BlockType.FIGURE and isinstance(block, FigureBlock):
                    figure_text = []
                    if block.caption:
                        figure_text.append(f"Caption: {block.caption}")
                    if block.alt_text:
                        figure_text.append(f"Alt text: {block.alt_text}")
                    if figure_text:
                        current_texts.append("\n".join(figure_text))

                elif block.type == BlockType.TABLE and isinstance(block, TableBlock):
                    if block.summary:
                        current_texts.append(block.summary)

            full_text = "\n".join(t for t in current_texts if t.strip()).strip()
            if full_text:
                chunks.append(
                    Chunk(
                        chunk_id=f"{document.document_id}_{len(chunks)+1}",
                        text=full_text,
                        metadata=current_metadata,
                    )
                )

        return chunks