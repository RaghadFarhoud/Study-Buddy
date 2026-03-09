from __future__ import annotations

from typing import List

from app.domain.models import CanonicalDocument, Section, BlockType
from app.normalizers.base import NormalizationPass


class SectionBoundaryPass(NormalizationPass):

    def apply(self, document: CanonicalDocument) -> CanonicalDocument:
        new_sections: List[Section] = []

        for section in document.sections:
            split_sections = self._split_section_if_needed(section)
            new_sections.extend(split_sections)

        document.sections = self._reindex_sections(new_sections)
        return document


    def _split_section_if_needed(self, section: Section) -> List[Section]:

        if not section.blocks:
            return [section]

        result_sections: List[Section] = []

        current_section = Section(
            title=section.title,
            path=section.path.copy(),
            blocks=[]
        )

        blocks = section.blocks

        for idx, block in enumerate(blocks):

            if self._is_new_section_boundary(blocks, idx, block):

                # إغلاق القسم الحالي
                current_section.blocks = self._reindex_blocks(current_section.blocks)
                result_sections.append(current_section)

                new_title = (block.text or "").strip()

                current_section = Section(
                    title=new_title,
                    path=[new_title],
                    blocks=[]
                )

                continue

            block.section_path = current_section.path.copy()
            current_section.blocks.append(block)

        current_section.blocks = self._reindex_blocks(current_section.blocks)
        result_sections.append(current_section)

        return [sec for sec in result_sections if sec.blocks]


    def _is_new_section_boundary(self, blocks, index: int, block) -> bool:

        if block.type != BlockType.PARAGRAPH:
            return False

        text = (block.text or "").strip()
        if not text:
            return False

        style_name = (block.metadata.get("style_name") or "").lower()
        words = text.split()

        # عنوان قصير نسبيًا
        if len(words) < 2 or len(words) > 8:
            return False

        # ليس عنصر قائمة
        if style_name.startswith("list"):
            return False

        # لا نسمح بالجمل الطويلة
        if len(text) > 60:
            return False

        # لا نعتبر الجمل المنتهية بعلامات وصفية
        if text.endswith("،") or text.endswith(";") or text.endswith("؛"):
            return False

        # يجب أن يليها محتوى وصفي
        if not self._has_following_descriptive_content(blocks, index):
            return False

        # يجب أن يكون قبلها محتوى كاف يدل أن القسم السابق انتهى
        if not self._has_preceding_section_like_content(blocks, index):
            return False

        return True


    def _has_following_descriptive_content(self, blocks, index: int) -> bool:

        descriptive_count = 0

        for next_block in blocks[index + 1:index + 5]:

            if next_block.type != BlockType.PARAGRAPH:
                continue

            text = (next_block.text or "").strip()
            if not text:
                continue

            if len(text.split()) >= 8:
                descriptive_count += 1

        return descriptive_count >= 1


    def _has_preceding_section_like_content(self, blocks, index: int) -> bool:

        prev_window = blocks[max(0, index - 5):index]

        if not prev_window:
            return False

        list_count = 0
        content_count = 0

        for prev_block in prev_window:

            if prev_block.type in {BlockType.NUMBERED_LIST, BlockType.BULLET_LIST}:
                list_count += 1

            if prev_block.type in {
                BlockType.PARAGRAPH,
                BlockType.NUMBERED_LIST,
                BlockType.BULLET_LIST,
                BlockType.TABLE,
                BlockType.FIGURE,
                BlockType.FIGURE_DESCRIPTION,
            }:
                content_count += 1

        # حالة شائعة: بعد قائمة "المطلوب"
        if list_count >= 2:
            return True

        return content_count >= 3


    def _reindex_sections(self, sections: List[Section]) -> List[Section]:
        for section in sections:
            section.blocks = self._reindex_blocks(section.blocks)
        return sections


    def _reindex_blocks(self, blocks: List) -> List:
        for idx, block in enumerate(blocks, start=1):
            block.order = idx
        return blocks