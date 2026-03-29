from app.extractors.pptx_extractor import PptxExtractor

import  json

extractor = PptxExtractor(image_output_dir="output_pptx/images")
doc = extractor.extract("lecture.pptx")

 

print(json.dumps(doc.model_dump(), indent=2, ensure_ascii=False))