from __future__ import annotations

import re
from typing import List


class PropositionRefiner:
    def refine(self, text: str) -> List[str]:
        text = (text or "").strip()
        if not text:
            return []

        # تقسيم أولي إلى جمل
        sentences = self._split_sentences(text)

        # تفكيك الجمل الطويلة ل أجزاء أدق
        refined: List[str] = []

        for sentence in sentences:
            parts = self._split_long_sentence(sentence)
            for part in parts:
                cleaned = self._cleanup(part)
                if self._is_valid_proposition(cleaned):
                    refined.append(cleaned)

        return refined

    def _split_sentences(self, text: str) -> List[str]:
        parts = re.split(r"(?<=[\.\!\؟\?؛])\s+", text)
        return [p.strip() for p in parts if p.strip()]

    def _split_long_sentence(self, sentence: str) -> List[str]:
        sentence = sentence.strip()
        if not sentence:
            return []

        # إذا كانت الجملة قصيرة نتركها كما هي
        if len(sentence) <= 180:
            return [sentence]

        # تقسيم على روابط شائعة
        split_patterns = [
            r"\s+و(?:في|من|على|ضمن)\s+",
            r"\s+وفي\s+",
            r"\s+ويعيد\s+",
            r"\s+ويحق\s+",
            r"\s+ويحتوي\s+",
            r"\s+وتحتوي\s+",
            r"\s+وترسل\s+",
            r"\s+وتخاطب\s+",
            r"\s+وتتمثل\s+",
            r"\s+بحيث\s+",
        ]

        parts = [sentence]

        for pattern in split_patterns:
            new_parts: List[str] = []
            for part in parts:
                split_result = re.split(pattern, part)
                split_result = [x.strip() for x in split_result if x.strip()]
                if split_result:
                    new_parts.extend(split_result)
                else:
                    new_parts.append(part)
            parts = new_parts

        # لو التقسيم أعطى أجزاء قصيرة كتير نرجع للجملة الأصلية
        valid_parts = [p for p in parts if len(p) >= 20]
        if not valid_parts:
            return [sentence]

        return valid_parts

    def _cleanup(self, text: str) -> str:
        text = text.strip()
        text = re.sub(r"\s+", " ", text)
        return text.strip(" ،؛.")

    def _is_valid_proposition(self, text: str) -> bool:
        if not text:
            return False

        if len(text) < 20:
            return False

        markers = [
            "يجب",
            "يمكن",
            "يسمح",
            "يُسمح",
            "يعتمد",
            "تحتوي",
            "ترتبط",
            "يحق",
            "يستطيع",
            "يَنفذ",
            "يعيد",
            "يفتح",
            "يطلع",
            "يعدل",
            "تخزن",
            "تحفظ",
        ]

        return any(marker in text for marker in markers)