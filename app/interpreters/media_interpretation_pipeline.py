from __future__ import annotations

from typing import List

from app.domain.models import CanonicalDocument
from app.interpreters.base import Interpreter


class MediaInterpretationPipeline:

    def __init__(self, interpreters: List[Interpreter]):
        self.interpreters = interpreters

    def run(self, document: CanonicalDocument) -> CanonicalDocument:
        for interpreter in self.interpreters:
             try:
                 document = interpreter.interpret(document)
             except Exception as e:
                print(f"[WARN] Interpreter {interpreter.__class__.__name__} failed: {e}")
        return document