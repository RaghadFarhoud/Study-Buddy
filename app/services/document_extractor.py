from __future__ import annotations

from abc import ABC, abstractmethod
from app.domain.models import CanonicalDocument


class DocumentExtractor(ABC):
    @abstractmethod
    def extract(self, file_path: str) -> CanonicalDocument:
        raise NotImplementedError