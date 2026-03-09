from __future__ import annotations

from typing import List

from app.domain.models import CanonicalDocument
from app.interpreters.base import Interpreter


class MediaInterpretationPipeline:

    def __init__(self, interpreters: List[Interpreter]):
        self.interpreters = interpreters

    def run(self, document: CanonicalDocument) -> CanonicalDocument:

        for interpreter in self.interpreters:
            document = interpreter.interpret(document)

        return document