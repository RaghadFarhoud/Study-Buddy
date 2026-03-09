from __future__ import annotations

from app.extractors.docx_extractor import DocxExtractor
from app.enrichers.basic_image_enricher import BasicImageEnricher, StubImageDescriber
from app.enrichers.caption_linker import CaptionLinker
from app.pipeline.ingestion_pipeline import IngestionPipeline
from app.transformers.study_text_transformer import StudyTextTransformer
from pathlib import Path


def main():
    extractor = DocxExtractor(image_output_dir="output/images")
    enricher = BasicImageEnricher(StubImageDescriber())
    caption_linker = CaptionLinker()

    pipeline = IngestionPipeline(
        extractor=extractor,
        image_enricher=enricher,
        caption_linker=caption_linker,
    )

    document = pipeline.run("lecture.docx")

    transformer = StudyTextTransformer()
    study_text = transformer.transform(document)

    print("=" * 80)
    print(study_text.full_text)
    print("=" * 80)

    Path("output/study_text.txt").write_text(
    study_text.full_text,
    encoding="utf-8"
    )
if __name__ == "__main__":
    main()