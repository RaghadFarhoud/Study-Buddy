from __future__ import annotations

from abc import ABC, abstractmethod

from app.domain.models import CanonicalDocument


class NormalizationPass(ABC):
    @abstractmethod
    def apply(self, document: CanonicalDocument) -> CanonicalDocument:
        raise NotImplementedError