from __future__ import annotations

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class StudyTextSection(BaseModel):
    title: Optional[str] = None
    section_path: List[str] = Field(default_factory=list)
    text: str
    metadata: Dict[str, Any] = Field(default_factory=dict)


class StudyTextView(BaseModel):
    document_id: str
    title: Optional[str] = None
    full_text: str
    sections: List[StudyTextSection] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class RagChunk(BaseModel):
    chunk_id: str
    document_id: str
    chunk_type: str
    text: str
    section_path: List[str] = Field(default_factory=list)
    source_file: str
    block_ids: List[str] = Field(default_factory=list)
    has_figure: bool = False
    has_table: bool = False
    metadata: Dict[str, Any] = Field(default_factory=dict)


class RagChunkView(BaseModel):
    document_id: str
    chunks: List[RagChunk] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)