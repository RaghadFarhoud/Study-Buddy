from __future__ import annotations

import argparse

from app.extractors.docx_extractor import DocxExtractor
from app.enrichers.basic_image_enricher import BasicImageEnricher, StubImageDescriber
from app.enrichers.caption_linker import CaptionLinker
from app.pipeline.ingestion_pipeline import IngestionPipeline


def main():
    parser = argparse.ArgumentParser(description="DOCX ingestion pipeline")
    parser.add_argument("file", help="Path to DOCX file")
    parser.add_argument("--out", default="output/result.json", help="Output JSON path")
    args = parser.parse_args()

    extractor = DocxExtractor(image_output_dir="output/images")
    enricher = BasicImageEnricher(StubImageDescriber())
    caption_linker = CaptionLinker()

    pipeline = IngestionPipeline(
        extractor=extractor,
        image_enricher=enricher,
        caption_linker=caption_linker,
    )

    document = pipeline.run(args.file)
    pipeline.save_json(document, args.out)

    print(f"Done. JSON saved to: {args.out}")


if __name__ == "__main__":
    main()