from __future__ import annotations

from typing import List

from app.domain.models import (
    CanonicalDocument,
    BaseBlock,
    FigureBlock,
    BlockType
)

from app.interpreters.base import Interpreter


class FigureInterpreter(Interpreter):

    def interpret(self, document: CanonicalDocument) -> CanonicalDocument:

        for section in document.sections:

            new_blocks: List[BaseBlock] = []

            for i, block in enumerate(section.blocks):

                new_blocks.append(block)

                if block.type != BlockType.FIGURE:
                    continue

                figure_block: FigureBlock = block

                context_text = self._get_nearby_context(section.blocks, i)

                description_text = self._generate_description(
                    figure_block,
                    context_text
                )

                desc_block = BaseBlock(
                    id=f"{figure_block.id}_desc",
                    type=BlockType.FIGURE_DESCRIPTION,
                    order=block.order + 1,
                    #order = block.order
                    text=description_text,
                    section_path=section.path.copy(),
                    metadata={
                        "figure_id": figure_block.id,
                        "generated": True
                    }
                )

                new_blocks.append(desc_block)

            section.blocks = self._reindex_blocks(new_blocks)

        return document

    def _get_nearby_context(self, blocks, index: int) -> str:

        context_parts = []

        for offset in range(1, 3):

            prev_i = index - offset
            if prev_i >= 0:
                prev_block = blocks[prev_i]
                if prev_block.text:
                    context_parts.append(prev_block.text)

        return " ".join(context_parts)

    def _generate_description(self, figure: FigureBlock, context: str) -> str:

        image_name = figure.image_name or "image"

        if context:
            return f"شرح الصورة: هذه صورة مستخرجة من المستند ({image_name}). السياق القريب: {context}"

        return f"شرح الصورة: هذه صورة مستخرجة من المستند ({image_name})."

    def _reindex_blocks(self, blocks: List[BaseBlock]) -> List[BaseBlock]:

        for idx, block in enumerate(blocks, start=1):
            block.order = idx

        return blocks