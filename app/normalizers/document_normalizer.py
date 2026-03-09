from __future__ import annotations

from typing import List

from app.domain.models import CanonicalDocument
from app.normalizers.base import NormalizationPass


class DocumentNormalizer:
    def __init__(self, passes: List[NormalizationPass]):
        self.passes = passes

    def normalize(self, document: CanonicalDocument) -> CanonicalDocument:
        normalized = document

        applied_passes: list[str] = []

        for normalization_pass in self.passes:
            normalized = normalization_pass.apply(normalized)
            applied_passes.append(normalization_pass.__class__.__name__)

        metadata = dict(normalized.metadata)
        metadata["normalized"] = True
        metadata["normalization_passes"] = applied_passes
        normalized.metadata = metadata

        return normalized