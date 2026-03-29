from __future__ import annotations

from app.builders.multi_level_chunk_builder import MultiLevelChunkBuilder
from pydantic import BaseModel

from app.domain.models import CanonicalDocument
from app.domain.outputs import MultiLevelChunkDocument, StudyTextDocument
from app.pipeline.ingestion_pipeline import IngestionPipeline
from app.interpreters.media_interpretation_pipeline import MediaInterpretationPipeline
from app.builders.study_text_builder import StudyTextBuilder
from app.domain.outputs import StudyTextDocument, MultiLevelChunkDocument, EducationalUnitDocument
from app.builders.educational_unit_builder import EducationalUnitBuilder

class DocumentProcessingResult(BaseModel):

    canonical_document: CanonicalDocument
    study_text: StudyTextDocument
    chunks: MultiLevelChunkDocument
    educational_units: EducationalUnitDocument  


class DocumentProcessingService:

    def __init__(
        self,
        ingestion_pipeline: IngestionPipeline,
        media_pipeline: MediaInterpretationPipeline,
        study_text_builder: StudyTextBuilder,
        chunk_builder: MultiLevelChunkBuilder,
        educational_unit_builder: EducationalUnitBuilder
    ):

        self.ingestion_pipeline = ingestion_pipeline
        self.media_pipeline = media_pipeline
        self.study_text_builder = study_text_builder
        self.chunk_builder = chunk_builder
        self.educational_unit_builder = educational_unit_builder

    def process(self, file_path: str) -> DocumentProcessingResult:

        document = self.ingestion_pipeline.run(file_path)

        document = self.media_pipeline.run(document)

        study_text = self.study_text_builder.build(document)

        chunks = self.chunk_builder.build(document)
        educational_units = self.educational_unit_builder.build(document)
 
        return DocumentProcessingResult(
            canonical_document=document,
            study_text=study_text,
            chunks=chunks,
            educational_units=educational_units
        )