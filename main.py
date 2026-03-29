from __future__ import annotations
from app.extractors.pptx_extractor import PptxExtractor
import argparse
import json
from pathlib import Path

from app.extractors.docx_extractor import DocxExtractor
from app.enrichers.caption_linker import CaptionLinker
from app.pipeline.ingestion_pipeline import IngestionPipeline
from app.builders.educational_unit_builder import EducationalUnitBuilder

from app.normalizers.document_normalizer import DocumentNormalizer
from app.normalizers.passes.cleanup_pass import CleanupPass
from app.normalizers.passes.heading_normalization_pass import HeadingNormalizationPass
from app.normalizers.passes.duplicate_suppression_pass import DuplicateSuppressionPass
from app.normalizers.passes.section_promotion_pass import SectionPromotionPass
from app.normalizers.passes.section_boundary_pass import SectionBoundaryPass
from app.normalizers.passes.repeated_page_noise_pass import RepeatedPageNoisePass
from app.normalizers.passes.broken_paragraph_merge_pass import BrokenParagraphMergePass
from app.normalizers.passes.diagram_noise_filter_pass import DiagramNoiseFilterPass
# from app.normalizers.passes.lecture_cleanup_pass import LectureCleanupPass

from app.interpreters.media_interpretation_pipeline import MediaInterpretationPipeline
from app.interpreters.figure_interpreter import FigureInterpreter
from app.interpreters.table_interpreter import TableInterpreter

from app.builders.study_text_builder import StudyTextBuilder
from app.services.document_processing_service import DocumentProcessingService
from app.builders.multi_level_chunk_builder import MultiLevelChunkBuilder




def build_docx_service(out_dir: Path) -> DocumentProcessingService:
    extractor = DocxExtractor(image_output_dir=str(out_dir / "images"))
    caption_linker = CaptionLinker()

    normalizer = DocumentNormalizer(
        passes=[
            CleanupPass(),
            RepeatedPageNoisePass(),
            BrokenParagraphMergePass(),
            DiagramNoiseFilterPass(),
            HeadingNormalizationPass(),
            DuplicateSuppressionPass(),
            SectionPromotionPass(),
            SectionBoundaryPass(),
        ]
    )

    ingestion_pipeline = IngestionPipeline(
        extractor=extractor,
        image_enricher=None,
        caption_linker=caption_linker,
        normalizer=normalizer,
    )

    media_pipeline = MediaInterpretationPipeline(
        interpreters=[
            FigureInterpreter(),
            TableInterpreter(),
        ]
    )

    study_text_builder = StudyTextBuilder()
    chunk_builder = MultiLevelChunkBuilder(max_paragraph_chars=1200)
    educational_unit_builder = EducationalUnitBuilder()

    return DocumentProcessingService(
        ingestion_pipeline=ingestion_pipeline,
        media_pipeline=media_pipeline,
        study_text_builder=study_text_builder,
        chunk_builder=chunk_builder,
        educational_unit_builder=educational_unit_builder,
    )
def build_pptx_service(out_dir: Path) -> DocumentProcessingService:
    extractor = PptxExtractor(image_output_dir=str(out_dir / "images"))

    ingestion_pipeline = IngestionPipeline(
        extractor=extractor,
        image_enricher=None,
        caption_linker=None,
        normalizer=None,
    )

    media_pipeline = MediaInterpretationPipeline(
        interpreters=[
            FigureInterpreter(),
            TableInterpreter(),
        ]
    )

    study_text_builder = StudyTextBuilder()
    chunk_builder = MultiLevelChunkBuilder(max_paragraph_chars=1200)
    educational_unit_builder = EducationalUnitBuilder()

    return DocumentProcessingService(
        ingestion_pipeline=ingestion_pipeline,
        media_pipeline=media_pipeline,
        study_text_builder=study_text_builder,
        chunk_builder=chunk_builder,
        educational_unit_builder=educational_unit_builder,
    )
# def main():

#     parser = argparse.ArgumentParser(description="Document processing pipeline")
#     parser.add_argument("file", help="Path to input DOCX file")
#     parser.add_argument("--out-dir", default="output", help="Output directory")

#     args = parser.parse_args()

#     out_dir = Path(args.out_dir)
#     out_dir.mkdir(parents=True, exist_ok=True)

#     extractor = DocxExtractor(image_output_dir=str(out_dir / "images"))
#     caption_linker = CaptionLinker()
#     normalizer = DocumentNormalizer(
#         passes=[
#             CleanupPass(),
#             # LectureCleanupPass(),
#             RepeatedPageNoisePass(),
#             BrokenParagraphMergePass(),
#             DiagramNoiseFilterPass(),
#             HeadingNormalizationPass(),
#             DuplicateSuppressionPass(),
#             SectionPromotionPass(),
#             SectionBoundaryPass(),
#         ]
#     )

#     ingestion_pipeline = IngestionPipeline(
#         extractor=extractor,
#         image_enricher=None,
#         caption_linker=caption_linker,
#         normalizer=normalizer,
#     )

#     media_pipeline = MediaInterpretationPipeline(
#         interpreters=[
#             FigureInterpreter(),
#             TableInterpreter(),
#         ]
#     )

#     study_text_builder = StudyTextBuilder()
#     chunk_builder = MultiLevelChunkBuilder(max_paragraph_chars=1200)
#     educational_unit_builder = EducationalUnitBuilder()

#     service = DocumentProcessingService(
#         ingestion_pipeline=ingestion_pipeline,
#         media_pipeline=media_pipeline,
#         study_text_builder=study_text_builder,
#         chunk_builder=chunk_builder,
#         educational_unit_builder=educational_unit_builder
#     )

#     result = service.process(args.file)

#     canonical_path = out_dir / "canonical_document.json"
#     study_text_json_path = out_dir / "study_text.json"
#     study_text_txt_path = out_dir / "study_text.txt"
#     chunks_json_path = out_dir / "chunks.json"
#     educational_units_json_path = out_dir / "educational_units.json"

#     canonical_path.write_text(
#         json.dumps(result.canonical_document.model_dump(), indent=2, ensure_ascii=False),
#         encoding="utf-8",
#     )

#     study_text_json_path.write_text(
#         json.dumps(result.study_text.model_dump(), indent=2, ensure_ascii=False),
#         encoding="utf-8",
#     )

#     study_text_txt_path.write_text(
#         result.study_text.full_text,
#         encoding="utf-8",
#     )

#     chunks_json_path.write_text(
#     json.dumps(result.chunks.model_dump(), indent=2, ensure_ascii=False),
#     encoding="utf-8",
#     )
#     educational_units_json_path.write_text(
#     json.dumps(result.educational_units.model_dump(), indent=2, ensure_ascii=False),
#     encoding="utf-8",
#     )

#     print(f"Canonical document saved to: {canonical_path}")
#     print(f"Study text JSON saved to: {study_text_json_path}")
#     print(f"Study text TXT saved to: {study_text_txt_path}")
#     print(f"Chunks JSON saved to: {chunks_json_path}")
#     print(f"Educational units JSON saved to: {educational_units_json_path}")
def main():
    parser = argparse.ArgumentParser(description="Document processing pipeline")
    parser.add_argument("file", help="Path to input DOCX or PPTX file")
    parser.add_argument("--out-dir", default="output", help="Output directory")

    args = parser.parse_args()

    input_path = Path(args.file)
    suffix = input_path.suffix.lower()

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    if suffix == ".docx":
        service = build_docx_service(out_dir)
    elif suffix == ".pptx":
        service = build_pptx_service(out_dir)
    else:
        raise ValueError(f"Unsupported file type: {suffix}. Only .docx and .pptx are supported.")

    result = service.process(str(input_path))

    canonical_path = out_dir / "canonical_document.json"
    study_text_json_path = out_dir / "study_text.json"
    study_text_txt_path = out_dir / "study_text.txt"
    chunks_json_path = out_dir / "chunks.json"
    educational_units_json_path = out_dir / "educational_units.json"

    canonical_path.write_text(
        json.dumps(result.canonical_document.model_dump(), indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    study_text_json_path.write_text(
        json.dumps(result.study_text.model_dump(), indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    study_text_txt_path.write_text(
        result.study_text.full_text,
        encoding="utf-8",
    )

    chunks_json_path.write_text(
        json.dumps(result.chunks.model_dump(), indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    educational_units_json_path.write_text(
        json.dumps(result.educational_units.model_dump(), indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    print(f"Canonical document saved to: {canonical_path}")
    print(f"Study text JSON saved to: {study_text_json_path}")
    print(f"Study text TXT saved to: {study_text_txt_path}")
    print(f"Chunks JSON saved to: {chunks_json_path}")
    print(f"Educational units JSON saved to: {educational_units_json_path}")



if __name__ == "__main__":
    main()