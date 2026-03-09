from __future__ import annotations

from abc import ABC, abstractmethod
from app.domain.models import CanonicalDocument


class Interpreter(ABC):

    @abstractmethod
    def interpret(self, document: CanonicalDocument) -> CanonicalDocument:
        pass