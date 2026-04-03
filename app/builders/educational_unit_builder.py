from __future__ import annotations

import re
from typing import List, Optional

from app.domain.models import CanonicalDocument, BlockType
from app.domain.outputs import EducationalUnitDocument, EducationalUnitItem
from app.builders.proposition_refiner import PropositionRefiner


class EducationalUnitBuilder:
    def __init__(self):
        self.proposition_refiner = PropositionRefiner()

    def build(self, document: CanonicalDocument) -> EducationalUnitDocument:
        units: List[EducationalUnitItem] = []
        counter = 1

        for section in document.sections:
            if not section.blocks:
                continue

            for block in section.blocks:
                extracted = self._extract_units_from_block(
                    document=document,
                    section_title=section.title,
                    section_path=section.path,
                    block=block,
                    counter_start=counter,
                )

                units.extend(extracted)
                counter += len(extracted)

        units = self._postprocess_units(units)

        return EducationalUnitDocument(
            document_id=document.document_id,
            source_type=document.source_type.value,
            source_file=document.source_file,
            units=units,
            metadata={
                "unit_count": len(units),
                "unit_types": [
                    "requirement",
                    "permission",
                    "procedure",
                    "concept",
                    "fact",
                    "figure_insight",
                ],
            },
        )

    def _extract_units_from_block(
        self,
        *,
        document: CanonicalDocument,
        section_title: str,
        section_path: List[str],
        block,
        counter_start: int,
    ) -> List[EducationalUnitItem]:
        units: List[EducationalUnitItem] = []

        # 1) القوائم
        if block.type in {BlockType.BULLET_LIST, BlockType.NUMBERED_LIST}:
            items = getattr(block, "items", None) or []
            local_counter = counter_start
            parent_text: Optional[str] = None

            for item in items:
                text = (getattr(item, "text", "") or "").strip()
                if not text:
                    continue

                level = getattr(item, "level", 0) or 0

                # عنصر أب
                if level == 0:
                    parent_text = text

                    if len(text.split()) <= 3:
                        continue

                    # إن كان نصًا تنظيميًا/ضعيفًا لا نحوله لوحدة مستقلة
                    if self._should_skip_unit_text(text) or self._is_structural_label(text):
                        continue

                    final_text = text

                # عنصر فرعي: ندمجه مع الأب إن وجد
                else:
                    final_text = self._combine_parent_child(parent_text, text)

                if self._should_skip_unit_text(final_text):
                    continue

                unit_type = self._classify_unit_type(
                    final_text,
                    source_type=block.type.value,
                )

                units.append(
                    self._make_unit(
                        unit_id=f"{document.document_id}_unit_{local_counter}",
                        document_id=document.document_id,
                        section_title=section_title,
                        section_path=section_path,
                        unit_type=unit_type,
                        text=final_text,
                        source_block_ids=[block.id],
                        source_block_types=[block.type.value],
                    )
                )
                local_counter += 1

            return units

        # 2) شرح الصور
        if block.type == BlockType.FIGURE_DESCRIPTION:
            text = (getattr(block, "text", "") or "").strip()

            if text and not self._should_skip_unit_text(text):
                units.append(
                    self._make_unit(
                        unit_id=f"{document.document_id}_unit_{counter_start}",
                        document_id=document.document_id,
                        section_title=section_title,
                        section_path=section_path,
                        unit_type="figure_insight",
                        text=text,
                        source_block_ids=[block.id],
                        source_block_types=[block.type.value],
                    )
                )

            return units

        # 3) الجداول
        if block.type == BlockType.TABLE:
            summary = (getattr(block, "summary", "") or "").strip()

            if summary and not self._should_skip_unit_text(summary):
                units.append(
                    self._make_unit(
                        unit_id=f"{document.document_id}_unit_{counter_start}",
                        document_id=document.document_id,
                        section_title=section_title,
                        section_path=section_path,
                        unit_type="fact",
                        text=f"ملخص الجدول: {summary}",
                        source_block_ids=[block.id],
                        source_block_types=[block.type.value],
                    )
                )

            return units

        # 4) الفقرات
        if block.type == BlockType.PARAGRAPH:
            text = (getattr(block, "text", "") or "").strip()
            if not text:
                return units

            propositions = self.proposition_refiner.refine(text)

            local_counter = counter_start
            for prop in propositions:
                prop = prop.strip()
                if not prop:
                    continue

                if self._should_skip_unit_text(prop):
                    continue

                unit_type = self._classify_unit_type(
                    prop,
                    source_type=block.type.value,
                )

                units.append(
                    self._make_unit(
                        unit_id=f"{document.document_id}_unit_{local_counter}",
                        document_id=document.document_id,
                        section_title=section_title,
                        section_path=section_path,
                        unit_type=unit_type,
                        text=prop,
                        source_block_ids=[block.id],
                        source_block_types=[block.type.value],
                    )
                )
                local_counter += 1

        return units

    def _make_unit(
        self,
        *,
        unit_id: str,
        document_id: str,
        section_title: str,
        section_path: List[str],
        unit_type: str,
        text: str,
        source_block_ids: List[str],
        source_block_types: List[str],
    ) -> EducationalUnitItem:
        return EducationalUnitItem(
            unit_id=unit_id,
            document_id=document_id,
            section_title=section_title,
            section_path=section_path.copy(),
            unit_type=unit_type,
            text=text.strip(),
            source_block_ids=source_block_ids,
            source_block_types=source_block_types,
            metadata={},
        )

    def _postprocess_units(self, units: List[EducationalUnitItem]) -> List[EducationalUnitItem]:
        deduped: List[EducationalUnitItem] = []
        seen = set()

        for unit in units:
            text = (unit.text or "").strip()
            if not text:
                continue

            if self._should_skip_unit_text(text):
                continue

            key = (
                self._normalize(unit.section_title or ""),
                self._normalize(text),
                unit.unit_type,
            )

            if key in seen:
                continue

            seen.add(key)
            deduped.append(unit)

        return deduped

    def _combine_parent_child(self, parent: Optional[str], child: str) -> str:
        child = (child or "").strip()
        if not child:
            return ""

        if not parent:
            return child

        parent = parent.strip().rstrip(":")
        child = child.lstrip(":").strip()

        if not parent:
            return child

        return f"{parent}: {child}"

    def _should_skip_unit_text(self, text: str) -> bool:
        text_norm = self._normalize(text)

        # نصوص فارغة أو شديدة الضعف
        if not text_norm:
            return True

        if len(text_norm) <= 2:
            return True

        weak_literals = {
            "...",
            "…",
            "-",
            ":",
        }

        if text_norm in weak_literals:
            return True

        return False

    def _is_structural_label(self, text: str) -> bool:
       
        text_norm = self._normalize(text).rstrip(":")
        if text_norm.endswith(":"):
            return True

        structural_labels = {
             "outline",
             "overview",
             "summary",
             "conclusion",
             "introduction",
             "examples",
             "example",
             "attack examples",
             "vulnerabilities examples",
             "threats examples",
             "other objectives",
             "next lecture",
             "next lectures",
             "references",
             "discussion",
             "results",
             "definitions",
             "key points",
             "main points",
             "main objectives",
             "main topics",
             "main themes",
             "main themes",
             "main topics",
             "main objectives",
        }
        return any(word in text_norm for word in structural_labels)
    #     return (
    #     text_norm in structural_labels
    #     or text_norm.endswith("examples")
    #     or text_norm.endswith("objectives")
    # )

    def _classify_unit_type(self, text: str, source_type: str) -> str:
        text_norm = self._normalize(text)

        # figure handled earlier, but keep safety
        if source_type == "figure_description":
            return "figure_insight"
       

        # requirement / policy / prohibition
        if self._contains_any(
            text_norm,
            [
                "يجب",
                "must",
                "must not",
                "should",
                "required",
                "requirement",
                "prohibited",
                "not allowed",
                "forbidden",
            ],
        ):
            return "requirement"

        # permissions
        if self._contains_any(
            text_norm,
            [
                "يسمح",
                "يُسمح",
                "يمكن",
                "يحق",
                "يستطيع",
                "allow",
                "allows",
                "allowed",
                "can",
                "may",
                "permitted",
            ],
        ):
            return "permission"

        # procedures / processes / lifecycle / steps
        if self._contains_any(
            text_norm,
            [
                "خطوة",
                "خطوات",
                "إجراء",
                "عملية",
                "ينفذ",
                "يَنفذ",
                "يعالج",
                "يرسل",
                "يستقبل",
                "يطلب",
                "يدخل",
                "يسجل",
                "process",
                "procedure",
                "workflow",
                "step",
                "steps",
                "develop",
                "design",
                "implement",
                "monitor",
                "review",
                "test",
                "execute",
                "login",
                "request",
                "reply",
                "send",
                "receive",
                "draw",
                "blueprint",
                "analyze",

                "choose",
                "carry out",
                "train",
                "training",
                "awareness",
                
                "operate",

                "improve",

            ],
        ):
        
            return "procedure"
        if ":" in text:
            left_side = text.split(":", 1)[0].strip()
            if len(left_side.split()) <= 5:
                return "concept"
        # concepts / definitions
        if self._contains_any(
            text_norm,
            [
                "هو",
                "هي",
                "يعني",
                "يشير إلى",
                "يتكون",
                "يتألف",
                "يتمثل",
                "يعتمد",
                "ترتبط",
                "تحتوي",
                "is a",
                "is an",
                "is the",
                "refers to",
                "property that",
                "defined as",
                "definition",
                "consists",
                "contains",
                "composed",
                "architecture",
                "layer",
                "layers",
                "preservation of",
            ],
        ):
            return "concept"

        return "fact"

    def _normalize(self, text: str) -> str:
        text = text.strip()
        text = re.sub(r"\s+", " ", text)
        return text.lower()

    def _contains_any(self, text: str, patterns: List[str]) -> bool:
        return any(p.lower() in text for p in patterns)