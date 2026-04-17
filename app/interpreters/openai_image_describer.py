from __future__ import annotations

import base64
import mimetypes
from pathlib import Path

from openai import OpenAI

from app.services.image_describer import ImageDescriber


class OpenAIImageDescriber(ImageDescriber):
    def __init__(self, model: str = "gpt-4.1-mini"):
        self.client = OpenAI()
        self.model = model

    def describe(self, image_path: Path, context_text: str | None = None) -> str:
        if not image_path.exists():
            raise FileNotFoundError(f"Image not found: {image_path}")

        mime_type = self._guess_mime_type(image_path)
        image_b64 = self._encode_image(image_path)
        prompt = self._build_prompt(context_text=context_text)

        try:
            response = self.client.responses.create(
                model=self.model,
                input=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "input_text",
                                "text": prompt,
                            },
                            {
                                "type": "input_image",
                                "image_url": f"data:{mime_type};base64,{image_b64}",
                            },
                        ],
                    }
                ],
            )

            text = self._extract_text(response)

            if text:
                return text

            # fallback إذا عاد الرد فارغًا
            return self._fallback_description(context_text=context_text, image_path=image_path)

        except Exception as e:
            print(f"[WARN] OpenAIImageDescriber failed for {image_path.name}: {e}")
            return self._fallback_description(context_text=context_text, image_path=image_path)

    def _build_prompt(self, context_text: str | None = None) -> str:
        parts = [
            "أنت مساعد تعليمي متخصص في شرح الصور المستخرجة من المحاضرات.",
            "حلل الصورة واكتب وصفًا تعليميًا واضحًا وموجزًا ومفيدًا للطالب.",
            "ركّز على الفكرة الأساسية التي توضحها الصورة، والعناصر المهمة فيها، والعلاقات بين المكونات إن وجدت.",
            "إذا كانت الصورة مخططًا أو بنية معمارية أو شبكة أو تسلسل خطوات، فاشرح ذلك بوضوح.",
            "إذا كانت الصورة لا تضيف معلومة تعليمية مهمة، فاذكر ذلك باختصار.",
            "لا تنسخ السياق كما هو، بل استخدمه لفهم الصورة فقط.",
            "اكتب الناتج كنص دراسي جاهز للإدماج داخل المحتوى.",
        ]

        if context_text:
            parts.append("")
            parts.append("السياق النصي المرتبط بالصورة:")
            parts.append(context_text)

        return "\n".join(parts)

    def _extract_text(self, response) -> str:
        # الطريق الأسرع إن كانت المكتبة تدعمه
        text = getattr(response, "output_text", None)
        if text and text.strip():
            return text.strip()

        # fallback يدوي إذا لم يكن output_text معبأ
        outputs = getattr(response, "output", None) or []
        parts = []

        for item in outputs:
            contents = getattr(item, "content", None) or []
            for content in contents:
                content_type = getattr(content, "type", "")
                if content_type in {"output_text", "text"}:
                    value = getattr(content, "text", None)
                    if value and value.strip():
                        parts.append(value.strip())

        return "\n".join(parts).strip()

    def _fallback_description(self, context_text: str | None, image_path: Path) -> str:
        if context_text:
            return "توضّح الصورة عنصرًا بصريًا تعليميًا مرتبطًا بموضوع هذا القسم، وتساعد في شرح المثال أو البنية أو العلاقات المعروضة."
        return f"توضّح الصورة عنصرًا بصريًا تعليميًا مستخرجًا من الملف ({image_path.name})."

    def _guess_mime_type(self, image_path: Path) -> str:
        mime_type, _ = mimetypes.guess_type(str(image_path))
        if mime_type:
            return mime_type
        return "image/png"

    def _encode_image(self, image_path: Path) -> str:
        with image_path.open("rb") as f:
            return base64.b64encode(f.read()).decode("utf-8")