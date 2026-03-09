from __future__ import annotations

from pydantic import BaseModel

from app.domain.models import CanonicalDocument
from app.domain.outputs import StudyTextDocument
from app.pipeline.ingestion_pipeline import IngestionPipeline
from app.interpreters.media_interpretation_pipeline import MediaInterpretationPipeline
from app.builders.study_text_builder import StudyTextBuilder


class DocumentProcessingResult(BaseModel):
    canonical_document: CanonicalDocument
    study_text: StudyTextDocument


class DocumentProcessingService:

    def __init__(
        self,
        ingestion_pipeline: IngestionPipeline,
        media_pipeline: MediaInterpretationPipeline,
        study_text_builder: StudyTextBuilder,
    ):
        self.ingestion_pipeline = ingestion_pipeline
        self.media_pipeline = media_pipeline
        self.study_text_builder = study_text_builder

    def process(self, file_path: str) -> DocumentProcessingResult:

        document = self.ingestion_pipeline.run(file_path)

        document = self.media_pipeline.run(document)

        study_text = self.study_text_builder.build(document)

        return DocumentProcessingResult(
            canonical_document=document,
            study_text=study_text,
        )