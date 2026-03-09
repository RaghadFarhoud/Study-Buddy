from __future__ import annotations

from typing import List

from app.domain.models import CanonicalDocument, Section, BlockType
from app.normalizers.base import NormalizationPass


class SectionPromotionPass(NormalizationPass):

    def apply(self, document: CanonicalDocument) -> CanonicalDocument:
        if not document.sections:
            return document

        new_sections: List[Section] = []

        for section in document.sections:

            # نطبق الترقية فقط على Root
            if section.title != "Root":
                new_sections.append(section)
                continue

            promoted_sections = self._promote_root_section(section)
            new_sections.extend(promoted_sections)

        document.sections = self._reindex_sections(new_sections)
        return document


    def _promote_root_section(self, root_section: Section) -> List[Section]:

        result_sections: List[Section] = []
        root_buffer: List = []

        current_section: Section | None = None
        blocks = root_section.blocks

        for idx, block in enumerate(blocks):

            if self._is_promotable_heading_candidate(blocks, idx, block):

                if current_section is not None:
                    current_section.blocks = self._reindex_blocks(current_section.blocks)
                    result_sections.append(current_section)

                promoted_title = block.text.strip()

                current_section = Section(
                    title=promoted_title,
                    path=[promoted_title],
                    blocks=[]
                )

                continue

            if current_section is None:
                root_buffer.append(block)

            else:
                block.section_path = current_section.path.copy()
                current_section.blocks.append(block)

        if current_section is not None:
            current_section.blocks = self._reindex_blocks(current_section.blocks)
            result_sections.append(current_section)

        if root_buffer:
            cleaned_root = Section(
                title="Root",
                path=[],
                blocks=self._reindex_blocks(root_buffer)
            )
            result_sections.insert(0, cleaned_root)

        return result_sections


    def _is_promotable_heading_candidate(self, blocks, index: int, block) -> bool:

        if block.type != BlockType.PARAGRAPH:
            return False

        text = (block.text or "").strip()
        if not text:
            return False

        style_name = (block.metadata.get("style_name") or "").lower()
        words = text.split()

        # 1) لا نرقّي الجمل الطويلة
        if len(text) > 70:
            return False

        # 2) لا نرقّي الجمل المنتهية بنقطة
        if text.endswith(".") or text.endswith("،") or text.endswith(";") or text.endswith("؛"):
            return False

        # 3) لا نرقّي عناصر القوائم
        if style_name.startswith("list"):
            return False

        # 4) لا نرقّي body text
        if style_name == "body text":
            return False

        # 5) عدد كلمات مناسب لعنوان
        if len(words) < 2 or len(words) > 8:
            return False

        # 6) يجب وجود محتوى تابع
        if not self._has_following_content(blocks, index):
            return False

        # 7) لا نرقّي النصوص التي تبدو جملة وصفية
        punctuation_count = sum(text.count(ch) for ch in [",", ":", "(", ")", "—", "-", "–"])
        if punctuation_count > 1:
            return False

        return True


    def _has_following_content(self, blocks, index: int) -> bool:

        meaningful_count = 0

        for next_block in blocks[index + 1:index + 5]:

            if next_block.type in {
                BlockType.PARAGRAPH,
                BlockType.BULLET_LIST,
                BlockType.NUMBERED_LIST,
                BlockType.TABLE,
                BlockType.FIGURE,
                BlockType.FIGURE_DESCRIPTION,
            }:

                text = getattr(next_block, "text", None)

                if next_block.type in {
                    BlockType.TABLE,
                    BlockType.FIGURE,
                    BlockType.FIGURE_DESCRIPTION
                }:
                    meaningful_count += 1

                elif text and text.strip():
                    meaningful_count += 1

        return meaningful_count >= 1


    def _reindex_sections(self, sections: List[Section]) -> List[Section]:
        for section in sections:
            section.blocks = self._reindex_blocks(section.blocks)
        return sections


    def _reindex_blocks(self, blocks: List) -> List:
        for idx, block in enumerate(blocks, start=1):
            block.order = idx
        return blocks