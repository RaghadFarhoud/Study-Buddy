from __future__ import annotations

import json
from pathlib import Path

from app.domain.models import CanonicalDocument
from app.services.document_extractor import DocumentExtractor
from app.enrichers.basic_image_enricher import BasicImageEnricher
from app.enrichers.caption_linker import CaptionLinker


class IngestionPipeline:
    def __init__(
        self,
        extractor: DocumentExtractor,
        image_enricher: BasicImageEnricher | None = None,
        caption_linker: CaptionLinker | None = None,
    ):
        self.extractor = extractor
        self.image_enricher = image_enricher
        self.caption_linker = caption_linker

    def run(self, file_path: str) -> CanonicalDocument:
        document = self.extractor.extract(file_path)

        if self.caption_linker:
            document = self.caption_linker.link(document)

        if self.image_enricher:
            document = self.image_enricher.enrich(document)

        return document

    def save_json(self, document: CanonicalDocument, output_path: str) -> None:
        out = Path(output_path)
        out.parent.mkdir(parents=True, exist_ok=True)

        data = document.model_dump()

        out.write_text(
            json.dumps(data, indent=2, ensure_ascii=False),
            encoding="utf-8"
        )