from __future__ import annotations

from pathlib import Path

from app.domain.models import CanonicalDocument, BaseBlock, FigureBlock, BlockType
from app.services.image_describer import ImageDescriber


class StubImageDescriber(ImageDescriber):
    def describe(self, image_path: Path, context_text: str | None = None) -> str:
        base = f"هذه صورة مستخرجة من المستند: {image_path.name}."
        if context_text:
            return base + f" السياق القريب: {context_text[:200]}"
        return base


class BasicImageEnricher:
    def __init__(self, describer: ImageDescriber):
        self.describer = describer

    def enrich(self, document: CanonicalDocument) -> CanonicalDocument:
        for section in document.sections:
            new_blocks = []
            for idx, block in enumerate(section.blocks):
                new_blocks.append(block)

                if block.type == BlockType.FIGURE and isinstance(block, FigureBlock):
                    context_text = self._nearest_text(section.blocks, idx)
                    description = self.describer.describe(
                        Path(block.image_path),
                        context_text=context_text
                    )

                    desc_block = BaseBlock(
                        id=f"{block.id}_desc",
                        type=BlockType.FIGURE_DESCRIPTION,
                        order=block.order + 1,
                        text=description,
                        section_path=block.section_path.copy(),
                        metadata={
                            "figure_id": block.id,
                            "generated": True,
                        },
                    )
                    new_blocks.append(desc_block)

            # Re-order blocks safely after insertion
            for i, b in enumerate(new_blocks, start=1):
                b.order = i
            section.blocks = new_blocks

        return document

    def _nearest_text(self, blocks, index: int) -> str | None:
        # Search backward then forward for nearest paragraph
        for i in range(index - 1, -1, -1):
            if blocks[i].text:
                return blocks[i].text
        for i in range(index + 1, len(blocks)):
            if blocks[i].text:
                return blocks[i].text
        return None