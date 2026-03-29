from __future__ import annotations

import re
from typing import List

from app.domain.models import CanonicalDocument, Section, BaseBlock, BlockType


class BrokenParagraphMergePass:
    def apply(self, document: CanonicalDocument) -> CanonicalDocument:
        cleaned_sections: List[Section] = []

        for section in document.sections:
            merged_blocks = self._merge_blocks(section.blocks)

            cleaned_sections.append(
                Section(
                    title=section.title,
                    path=section.path.copy(),
                    blocks=self._reindex(merged_blocks),
                )
            )

        document.sections = cleaned_sections
        return document

    def _merge_blocks(self, blocks: List[BaseBlock]) -> List[BaseBlock]:
        if not blocks:
            return []

        result: List[BaseBlock] = []
        i = 0

        while i < len(blocks):
            current = blocks[i]

            if current.type != BlockType.PARAGRAPH or not self._has_text(current.text):
                result.append(current)
                i += 1
                continue

            merged_text = current.text.strip()
            j = i + 1

            while j < len(blocks):
                nxt = blocks[j]

                if nxt.type != BlockType.PARAGRAPH or not self._has_text(nxt.text):
                    break

                if self._looks_like_standalone_heading(nxt.text):
                    break

                if self._looks_like_list_item(nxt.text):
                    break

                if not self._should_merge(merged_text, nxt.text):
                    break

                merged_text = self._merge_texts(merged_text, nxt.text)
                j += 1

            current.text = merged_text
            result.append(current)
            i = j

        return result

    def _should_merge(self, left: str, right: str) -> bool:
        left = self._normalize(left)
        right = self._normalize(right)

        if not left or not right:
            return False

        if self._ends_like_complete_sentence(left):
            return False

        if len(left) <= 120:
            return True

        if self._starts_like_continuation(right):
            return True

        return False

    def _merge_texts(self, left: str, right: str) -> str:
        left = left.rstrip()
        right = right.lstrip()

        if left.endswith("-"):
            return left[:-1] + right

        return f"{left} {right}"

    def _looks_like_standalone_heading(self, text: str) -> bool:
        text = self._normalize(text)
        if not text:
            return False

        if text.endswith(":"):
            return True

        if len(text) <= 50 and not self._ends_like_complete_sentence(text):
            if not self._starts_like_continuation(text):
                return True

        return False

    def _looks_like_list_item(self, text: str) -> bool:
        text = self._normalize(text)
        return bool(re.match(r"^(\d+[\.\)]|\-|\•|\▪)\s*", text))

    def _ends_like_complete_sentence(self, text: str) -> bool:
        return self._normalize(text).endswith((".", "؟", "!", ":", "؛"))

    def _starts_like_continuation(self, text: str) -> bool:
        text = self._normalize(text)
        if not text:
            return False

        continuation_prefixes = [
            "و",
            "أو",
            "لكن",
            "ثم",
            "حيث",
            "التي",
            "الذي",
            "الذين",
            "لذلك",
            "بالإضافة",
        ]

        first_word = text.split()[0]

        if first_word in continuation_prefixes:
            return True

        if re.match(r"^[a-z\(]", text):
            return True

        return False

    def _normalize(self, text: str | None) -> str:
        if not text:
            return ""
        return re.sub(r"\s+", " ", text).strip()

    def _has_text(self, text: str | None) -> bool:
        return bool(self._normalize(text))

    def _reindex(self, blocks: List[BaseBlock]) -> List[BaseBlock]:
        for idx, block in enumerate(blocks, start=1):
            block.order = idx
        return blocks