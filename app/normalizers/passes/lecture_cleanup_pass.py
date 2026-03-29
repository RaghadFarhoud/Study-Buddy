from __future__ import annotations

import re
from collections import Counter
from typing import List

from app.domain.models import CanonicalDocument, Section, BaseBlock, BlockType


class LectureCleanupPass:
  
    def apply(self, document: CanonicalDocument) -> CanonicalDocument:
        cleaned_sections: List[Section] = []

        repeated_noise = self._detect_repeated_noise_candidates(document)

        for section in document.sections:
            filtered_blocks = self._remove_noise_blocks(section.blocks, repeated_noise)
            merged_blocks = self._merge_broken_paragraphs(filtered_blocks)

            reindexed = self._reindex_blocks(merged_blocks)

            cleaned_sections.append(
                Section(
                    title=section.title,
                    path=section.path.copy(),
                    blocks=reindexed,
                )
            )

        document.sections = cleaned_sections

        metadata = dict(document.metadata or {})
        passes = list(metadata.get("cleanup_notes", []))
        passes.append("LectureCleanupPass")
        metadata["cleanup_notes"] = passes
        document.metadata = metadata

        return document

    def _detect_repeated_noise_candidates(self, document: CanonicalDocument) -> set[str]:
        texts: List[str] = []

        for section in document.sections:
            for block in section.blocks:
                if block.type != BlockType.PARAGRAPH:
                    continue

                text = self._normalize_text(block.text)
                if not text:
                    continue

                if len(text) <= 40:
                    texts.append(text)

        counts = Counter(texts)

        repeated = {
            text
            for text, count in counts.items()
            if count >= 2 and self._looks_like_header_footer_noise(text)
        }

        return repeated

    def _remove_noise_blocks(
        self,
        blocks: List[BaseBlock],
        repeated_noise: set[str],
    ) -> List[BaseBlock]:
        kept: List[BaseBlock] = []

        for block in blocks:
            text = self._normalize_text(block.text)

            if block.type == BlockType.PARAGRAPH:
                if self._is_page_number(text):
                    continue

                if text in repeated_noise:
                    continue

                if self._is_low_value_noise(text):
                    continue

            kept.append(block)

        return kept

    def _merge_broken_paragraphs(self, blocks: List[BaseBlock]) -> List[BaseBlock]:
        if not blocks:
            return []

        merged: List[BaseBlock] = []
        i = 0

        while i < len(blocks):
            current = blocks[i]

            if current.type != BlockType.PARAGRAPH or not self._has_meaningful_text(current.text):
                merged.append(current)
                i += 1
                continue

            combined_text = current.text.strip()
            j = i + 1

            while j < len(blocks):
                nxt = blocks[j]

                if nxt.type != BlockType.PARAGRAPH or not self._has_meaningful_text(nxt.text):
                    break

                if not self._should_merge_paragraphs(combined_text, nxt.text):
                    break

                combined_text = self._merge_texts(combined_text, nxt.text)
                j += 1

            if j > i + 1:
                current.text = combined_text

            merged.append(current)
            i = j

        return merged

    def _should_merge_paragraphs(self, left: str, right: str) -> bool:
        left = (left or "").strip()
        right = (right or "").strip()

        if not left or not right:
            return False

        if self._looks_like_standalone_heading(right):
            return False

        if self._looks_like_list_item(right):
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

    def _reindex_blocks(self, blocks: List[BaseBlock]) -> List[BaseBlock]:
        for idx, block in enumerate(blocks, start=1):
            block.order = idx
        return blocks

    def _normalize_text(self, text: str | None) -> str:
        if not text:
            return ""
        text = re.sub(r"\s+", " ", text).strip()
        return text

    def _has_meaningful_text(self, text: str | None) -> bool:
        text = self._normalize_text(text)
        return bool(text)

    def _is_page_number(self, text: str) -> bool:
        if not text:
            return False

        if re.fullmatch(r"\d{1,3}", text):
            return True

        if re.fullmatch(r"\d{1,3}\s*/\s*\d{1,3}", text):
            return True

        return False

    def _looks_like_header_footer_noise(self, text: str) -> bool:
        if not text:
            return False

        patterns = [
            r"/[A-Za-z0-9\.\-_]+",
            r"ITE\.RBCs",
            r"د\.",
        ]

        return any(re.search(p, text) for p in patterns)

    def _is_low_value_noise(self, text: str) -> bool:
        if not text:
            return True


        if text in {"▪", "•", "", "←", "-", "--", "—"}:
            return True


        if len(text) <= 2:
            return True

        if len(text) <= 20 and re.fullmatch(r"[A-Za-z0-9\s\-\._/|]+", text):
            return True

        return False

    def _looks_like_standalone_heading(self, text: str) -> bool:
        text = self._normalize_text(text)
        if not text:
            return False

        if text.endswith(":"):
            return True

        if len(text) <= 60 and not self._ends_like_complete_sentence(text):
           
            return True

        return False

    def _looks_like_list_item(self, text: str) -> bool:
        text = self._normalize_text(text)
        if not text:
            return False

        return bool(
            re.match(r"^(\d+[\.\)]|\-|\•|\▪)\s*", text)
        )

    def _ends_like_complete_sentence(self, text: str) -> bool:
        text = self._normalize_text(text)
        return text.endswith((".", "؟", "!", ":", "؛"))

    def _starts_like_continuation(self, text: str) -> bool:
        text = self._normalize_text(text)
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

        # إن بدأت بحرف صغير إنكليزي أو بقوس/رمز
        if re.match(r"^[a-z\(]", text):
            return True

        return False