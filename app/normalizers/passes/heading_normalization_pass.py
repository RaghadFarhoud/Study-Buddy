from __future__ import annotations

import re
from typing import List

from app.domain.models import CanonicalDocument, Section, BaseBlock, BlockType


class HeadingNormalizationPass:
    """
    نسخة أكثر تحفظًا من heading normalization للمحاضرات الحقيقية.
    الهدف:
    - تقليل false positives في العناوين
    - عدم تحويل labels أو كسور الأسطر إلى sections
    """

    def apply(self, document: CanonicalDocument) -> CanonicalDocument:
        original_sections = document.sections
        rebuilt_sections: List[Section] = []

        current_section = Section(title="Root", path=[], blocks=[])
        rebuilt_sections.append(current_section)

        current_path: List[str] = []

        for section in original_sections:
            for idx, block in enumerate(section.blocks):
                if block.type == BlockType.HEADING:
                    title = self._clean_heading_text(block.text)
                    if not title:
                        continue

                    level = self._extract_heading_level(block)

                    current_path = current_path[: level - 1]
                    current_path.append(title)

                    current_section = Section(
                        title=title,
                        path=current_path.copy(),
                        blocks=[],
                    )
                    rebuilt_sections.append(current_section)
                    continue

                if self._should_promote_to_heading(section.blocks, idx, block):
                    title = self._clean_heading_text(block.text)
                    if not title:
                        current_section.blocks.append(block)
                        continue

                    level = 1
                    current_path = current_path[: level - 1]
                    current_path.append(title)

                    current_section = Section(
                        title=title,
                        path=current_path.copy(),
                        blocks=[],
                    )
                    rebuilt_sections.append(current_section)
                    continue

                current_section.blocks.append(block)

        document.sections = self._drop_empty_root_if_needed(rebuilt_sections)
        return document

    def _should_promote_to_heading(
        self,
        blocks: List[BaseBlock],
        index: int,
        block: BaseBlock,
    ) -> bool:
        if block.type != BlockType.PARAGRAPH:
            return False

        text = self._normalize(block.text)
        if not text:
            return False

        # لا نرقّي القوائم أو ما يشبهها
        if self._looks_like_list_item(text):
            return False

        # لا نرقّي أسطر قصيرة إنجليزية/diagram labels
        if self._looks_like_diagram_label(text):
            return False

        # لا نرقّي سطرًا يبدو continuation
        if self._looks_like_continuation(text):
            return False

        # لا نرقّي سطرًا طويلًا جدًا
        if len(text) > 90:
            return False

        # لا نرقّي سطرًا منتهيًا بشكل يبدو جملة عادية
        if self._looks_like_full_sentence(text) and not text.endswith(":"):
            return False

        # يجب أن يكون heading-like
        if not self._looks_like_heading_candidate(text):
            return False

        # ويجب أن يتبعه محتوى فعلي
        if not self._has_meaningful_following_content(blocks, index):
            return False

        return True

    def _looks_like_heading_candidate(self, text: str) -> bool:
        text = self._normalize(text)
        if not text:
            return False

        # ينتهي بنقطتين -> غالبًا عنوان/intro heading
        if text.endswith(":"):
            return True

        # عنوان قصير نسبيًا وليس جملة كاملة
        if len(text) <= 60 and not self._looks_like_full_sentence(text):
            return True

        return False

    def _has_meaningful_following_content(self, blocks: List[BaseBlock], index: int) -> bool:
        look_ahead = 3
        meaningful_count = 0

        for offset in range(1, look_ahead + 1):
            nxt_idx = index + offset
            if nxt_idx >= len(blocks):
                break

            nxt = blocks[nxt_idx]

            if nxt.type in {BlockType.PARAGRAPH, BlockType.BULLET_LIST, BlockType.NUMBERED_LIST}:
                text = self._normalize(nxt.text)
                if text and not self._looks_like_diagram_label(text):
                    meaningful_count += 1

        return meaningful_count >= 1

    def _looks_like_full_sentence(self, text: str) -> bool:
        text = self._normalize(text)

        if text.endswith((".", "؟", "!", "؛")):
            return True

        sentence_markers = [
            "هو",
            "هي",
            "كان",
            "كانت",
            "يكون",
            "تكون",
            "يمكن",
            "يجب",
            "يسمح",
            "يعتمد",
            "تخزن",
            "تحفظ",
            "contains",
            "is",
            "are",
            "can",
            "must",
            "should",
        ]

        return any(marker in text for marker in sentence_markers)

    def _looks_like_continuation(self, text: str) -> bool:
        text = self._normalize(text)
        if not text:
            return False

        first_word = text.split()[0]

        continuation_starts = {
            "و",
            "أو",
            "ثم",
            "لكن",
            "حيث",
            "التي",
            "الذي",
            "الذين",
            "لذلك",
            "كما",
            "أي",
        }

        if first_word in continuation_starts:
            return True

        if re.match(r"^[a-z\(]", text):
            return True

        return False

    def _looks_like_list_item(self, text: str) -> bool:
        return bool(re.match(r"^(\d+[\.\)]|\-|\•|\▪)\s*", text))

    def _looks_like_diagram_label(self, text: str) -> bool:
        t = text.strip().lower()

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
            "computer science",
            "geometry transformation",
            "viewing and projection",
            "texture and mapping",
            "drawing and clipping primitives",
            "local illumination and shading",
            "global rendering",
            "open gl",
        }

        if t in known_labels:
            return True

        if len(t) <= 35 and re.fullmatch(r"[A-Za-z0-9\s\-\._/|]+", t):
            return True

        return False

    def _clean_heading_text(self, text: str | None) -> str:
        text = self._normalize(text)

        # إزالة الرموز الزخرفية من البداية
        text = re.sub(r"^[\-\•\▪\\←\→\*]+", "", text).strip()

        return text

    def _extract_heading_level(self, block: BaseBlock) -> int:
        metadata = block.metadata or {}
        level = metadata.get("heading_level")
        if isinstance(level, int) and level > 0:
            return level
        return 1

    def _drop_empty_root_if_needed(self, sections: List[Section]) -> List[Section]:
        if not sections:
            return sections

        if len(sections) == 1:
            return sections

        first = sections[0]
        if first.title == "Root" and not first.blocks:
            return sections[1:]

        return sections

    def _normalize(self, text: str | None) -> str:
        if not text:
            return ""
        return re.sub(r"\s+", " ", text).strip()