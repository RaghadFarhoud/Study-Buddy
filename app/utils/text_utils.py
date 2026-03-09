from __future__ import annotations

import re


def clean_text(text: str) -> str:
    text = text.replace("\xa0", " ")
    text = re.sub(r"\s+", " ", text).strip()
    return text


def is_empty(text: str | None) -> bool:
    return not text or not text.strip()


def looks_like_caption(text: str) -> bool:
    if not text:
        return False
    lowered = text.strip().lower()
    return (
        lowered.startswith("figure")
        or lowered.startswith("fig.")
        or lowered.startswith("fig ")
        or lowered.startswith("شكل")
        or lowered.startswith("الشكل")
    )


def looks_like_numbered_item(text: str) -> bool:
    if not text:
        return False

    text = text.strip()

    patterns = [
        r"^\d+[\)\.\-]\s+",       # 1) xxx أو 1. xxx
        r"^[٠-٩]+[\)\.\-]\s+",    # ١) xxx أو ١. xxx
    ]

    return any(re.match(p, text) for p in patterns)

def looks_like_heading_by_text(text: str) -> bool:
    if not text:
        return False

    text = clean_text(text)
    if not text:
        return False

    # لا نعتبر عناصر القوائم عناوين
    if looks_like_numbered_item(text):
        return False

    # النصوص الطويلة ليست عناوين
    if len(text) > 70:
        return False

    # الجملة المنتهية بنقطة أو فاصلة غالبًا ليست عنوانًا
    if text.endswith(".") or text.endswith("،") or text.endswith(";") or text.endswith("؛"):
        return False

    words = text.split()

    # العنوان لا يكون كلمة واحدة عادة، ولا طويلًا جدًا
    if len(words) < 2 or len(words) > 8:
        return False

    heading_patterns = [
        r"^\d+(?:\.\d+)*\s+.+$",
        r"^[٠-٩]+(?:\.\d+)*\s+.+$",
        r"^الفصل\s+.+$",
        r"^المبحث\s+.+$",
        r"^المطلب\s+.+$",
        r"^العنوان\s+.+$",
        r"^مقدمة$",
        r"^خاتمة$",
        r"^نتائج$",
        r"^توصيات$",
        r"^المطلوب:?$",
    ]

    if any(re.match(p, text) for p in heading_patterns):
        return True

    # heuristic محافظة:
    # عنوان قصير بدون علامات ترقيم كثيرة
    punctuation_count = sum(text.count(ch) for ch in [",", ":", "(", ")", "—", "-", "–"])
    if punctuation_count > 1:
        return False

    return True
    """
    Heuristic heading detector for DOCX paragraphs with Normal style.
    """
    if not text:
        return False

    text = clean_text(text)
    if not text:
        return False

    # طويل جدًا => غالبًا ليس عنوانًا
    if len(text) > 80:
        return False

    # إذا انتهى بنقطة فغالبًا فقرة عادية
    if text.endswith(".") or text.endswith("،") or text.endswith(";") or text.endswith("؛"):
        return False

    # العناصر المرقمة ليست headings
    if looks_like_numbered_item(text):
        return False

    heading_patterns = [
        r"^\d+(\.\d+)*\s+.+$",      # 1 عنوان / 1.2 عنوان
        r"^[٠-٩]+(\.[٠-٩]+)*\s+.+$", 
        r"^الفصل\s+.+$",
        r"^المبحث\s+.+$",
        r"^المطلب\s+.+$",
        r"^العنوان\s+.+$",
        r"^مقدمة$",
        r"^خاتمة$",
        r"^نتائج$",
        r"^توصيات$",
    ]

    return any(re.match(p, text) for p in heading_patterns)

def is_meaningful_text(text: str | None) -> bool:
    if not text:
        return False

    cleaned = clean_text(text)
    if not cleaned:
        return False

    # تجاهل النصوص التافهة مثل "." أو "-" وحدها
    if cleaned in {".", "-", "_", "•", ":"}:
        return False

    return True