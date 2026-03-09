from __future__ import annotations

from app.extractors.docx_extractor import DocxExtractor
from app.enrichers.basic_image_enricher import BasicImageEnricher, StubImageDescriber
from app.enrichers.caption_linker import CaptionLinker
from app.pipeline.ingestion_pipeline import IngestionPipeline
from app.transformers.rag_chunk_transformer import RagChunkTransformer
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

    transformer = RagChunkTransformer(max_chars=1000)
    chunk_view = transformer.transform(document)

    print("=" * 80)
    print(f"Total chunks: {len(chunk_view.chunks)}")
    print("=" * 80)

    for chunk in chunk_view.chunks:
        print(f"Chunk ID: {chunk.chunk_id}")
        print(f"Chunk Type: {chunk.chunk_type}")
        print(f"Section Path: {chunk.section_path}")
        print(f"Has Figure: {chunk.has_figure}")
        print(f"Has Table: {chunk.has_table}")
        print("-" * 60)
        print(chunk.text)
        print("=" * 80)

    Path("output/rag_chunks.json").write_text(
    chunk_view.model_dump_json(indent=2),
    encoding="utf-8"
)

if __name__ == "__main__":
    main()