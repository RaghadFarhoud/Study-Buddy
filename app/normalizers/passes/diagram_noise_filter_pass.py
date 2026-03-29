from __future__ import annotations

import re
from typing import List

from app.domain.models import CanonicalDocument, Section, BaseBlock, BlockType


class DiagramNoiseFilterPass:
    def apply(self, document: CanonicalDocument) -> CanonicalDocument:
        cleaned_sections: List[Section] = []

        for section in document.sections:
            kept_blocks: List[BaseBlock] = []

            for block in section.blocks:
                text = self._normalize(block.text)

                if block.type == BlockType.PARAGRAPH and self._is_diagram_noise(text):
                    continue

                kept_blocks.append(block)

            cleaned_sections.append(
                Section(
                    title=section.title,
                    path=section.path.copy(),
                    blocks=self._reindex(kept_blocks),
                )
            )

        document.sections = cleaned_sections
        return document

    def _is_diagram_noise(self, text: str) -> bool:
        if not text:
            return False

        known_labels = {
            "input",
            "output",
            "model",
            "analysis",
            "processing",
            "analysis processing",
            "analysis processingmodel",
            "numerical image",
            "real image",
            "algoritmes",
            "algorithms",
            "synthesis",
            "image synthesis",
            "cg",
            "physics",
            "geometric mathhardware",
            "computer science",
            "geometry transformation",
            "viewing and projection",
            "texture and mapping",
            "drawing and clipping primitives",
            "local illumination and shading",
            "global rendering",
            "open gl",
        }

        normalized_lower = text.lower().strip()

        if normalized_lower in known_labels:
            return True

        if len(text) <= 35 and re.fullmatch(r"[A-Za-z0-9\s\-\._/|]+", text):
            return True

        if text in {"▪", "•", "", "←", "-", "--", "—"}:
            return True

        return False

    def _normalize(self, text: str | None) -> str:
        if not text:
            return ""
        return re.sub(r"\s+", " ", text).strip()

    def _reindex(self, blocks: List[BaseBlock]) -> List[BaseBlock]:
        for idx, block in enumerate(blocks, start=1):
            block.order = idx
        return blocks