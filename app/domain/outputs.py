from __future__ import annotations

from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


class StudyTextSection(BaseModel):
    title: str
    section_path: List[str] = Field(default_factory=list)
    text: str
    metadata: Dict[str, Any] = Field(default_factory=dict)


class StudyTextDocument(BaseModel):
    document_id: str
    source_type: str
    source_file: str
    title: Optional[str] = None
    full_text: str
    sections: List[StudyTextSection] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)