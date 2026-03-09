from __future__ import annotations

from app.domain.models import (
    CanonicalDocument,
    BlockType
)

from app.interpreters.base import Interpreter


class TableInterpreter(Interpreter):

    def interpret(self, document: CanonicalDocument) -> CanonicalDocument:

        for section in document.sections:

            for block in section.blocks:

                if block.type != BlockType.TABLE:
                    continue

                if block.summary:
                    continue

                rows = block.rows
                cols = block.cols

                block.summary = f"هذا جدول يحتوي على {rows} صفوف و {cols} أعمدة."

        return document