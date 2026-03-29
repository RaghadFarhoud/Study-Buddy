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



class MultiLevelChunkItem(BaseModel):
    chunk_id: str
    level: str  # proposition | paragraph | section
    document_id: str
    section_title: str
    section_path: List[str] = Field(default_factory=list)
    text: str
    source_block_ids: List[str] = Field(default_factory=list)
    block_types: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class MultiLevelChunkDocument(BaseModel):
    document_id: str
    source_type: str
    source_file: str
    chunks: List[MultiLevelChunkItem] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)

class EducationalUnitItem(BaseModel):
    unit_id: str
    document_id: str
    section_title: str
    section_path: List[str] = Field(default_factory=list)
    unit_type: str  # requirement | permission | procedure | concept | fact | figure_insight
    text: str
    source_block_ids: List[str] = Field(default_factory=list)
    source_block_types: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class EducationalUnitDocument(BaseModel):
    document_id: str
    source_type: str
    source_file: str
    units: List[EducationalUnitItem] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)