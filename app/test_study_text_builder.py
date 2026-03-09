from __future__ import annotations

from pathlib import Path

from app.extractors.docx_extractor import DocxExtractor
from app.enrichers.caption_linker import CaptionLinker
from app.pipeline.ingestion_pipeline import IngestionPipeline

from app.normalizers.document_normalizer import DocumentNormalizer
from app.normalizers.passes.cleanup_pass import CleanupPass
from app.normalizers.passes.heading_normalization_pass import HeadingNormalizationPass
from app.normalizers.passes.duplicate_suppression_pass import DuplicateSuppressionPass
from app.normalizers.passes.section_promotion_pass import SectionPromotionPass
from app.normalizers.passes.section_boundary_pass import SectionBoundaryPass

from app.interpreters.media_interpretation_pipeline import MediaInterpretationPipeline
from app.interpreters.figure_interpreter import FigureInterpreter
from app.interpreters.table_interpreter import TableInterpreter

from app.builders.study_text_builder import StudyTextBuilder


def main():

    extractor = DocxExtractor(image_output_dir="output/images")
    caption_linker = CaptionLinker()

    normalizer = DocumentNormalizer(
        passes=[
            CleanupPass(),
            HeadingNormalizationPass(),
            DuplicateSuppressionPass(),
            SectionPromotionPass(),
            SectionBoundaryPass(),
        ]
    )

    pipeline = IngestionPipeline(
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

    document = pipeline.run("lecture.docx")
    document = media_pipeline.run(document)

    builder = StudyTextBuilder()
    study_text = builder.build(document)

    out_dir = Path("output")
    out_dir.mkdir(parents=True, exist_ok=True)

    (out_dir / "study_text.txt").write_text(study_text.full_text, encoding="utf-8")

    (out_dir / "study_text.json").write_text(
        study_text.model_dump_json(indent=2),
        encoding="utf-8"
    )

    print("Study text saved to output/study_text.txt")
    print("Study text JSON saved to output/study_text.json")


if __name__ == "__main__":
    main()