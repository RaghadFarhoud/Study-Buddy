from __future__ import annotations

import re
from typing import List

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

        # 1) القوائم = وحدات تعليمية جاهزة
        if block.type in {BlockType.BULLET_LIST, BlockType.NUMBERED_LIST} :
            items = getattr(block, "items", None) or []
            local_counter = counter_start
            for item in items:
                text = (item.text or "").strip()

                if not text:
                    continue

            unit_type = self._classify_unit_type(text, source_type=block.type.value)

            units.append(
                self._make_unit(
                    unit_id=f"{document.document_id}_unit_{counter_start}",
                    document_id=document.document_id,
                    section_title=section_title,
                    section_path=section_path,
                    unit_type=unit_type,
                    text=text,
                    source_block_ids=[block.id],
                    source_block_types=[block.type.value],
                )
            )
            local_counter += 1
            return units

        # 2) شرح الصور
        if block.type == BlockType.FIGURE_DESCRIPTION:
            text = (getattr(block, "text", "") or "").strip()
            if text:
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

        # 3) الجداول - لو أردت اعتبار ملخص الجدول وحدة
        if block.type == BlockType.TABLE:
            summary = getattr(block, "summary", None)
            if summary:
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

                unit_type = self._classify_unit_type(prop, source_type=block.type.value)

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

    def _classify_unit_type(self, text: str, source_type: str) -> str:
        text_norm = self._normalize(text)

        # figure handled earlier, but keep safety
        if source_type == "figure_description":
            return "figure_insight"

        # requirements
        if self._contains_any(
            text_norm,
            [
                "يجب",
                "must",
                "should",
                "required",
                "requirement",
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

        # procedures / flow
        if self._contains_any(
            text_norm,
            [
                "يَنفذ",
                "ينفذ",
                "يعيد",
                "يرسل",
                "يطلب",
                "يفتح",
                "يدخل",
                "يسجل",
                "يعالج",
                "request",
                "reply",
                "process",
                "send",
                "receive",
                "login",
                "execute",
            ],
        ):
            return "procedure"

        # concepts / definitions / architecture
        if self._contains_any(
            text_norm,
            [
                "يعتمد",
                "يتكون",
                "يتألف",
                "تتمثل",
                "تحتوي",
                "ترتبط",
                "architecture",
                "consists",
                "contains",
                "composed",
                "layer",
                "layers",
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