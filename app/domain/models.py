from __future__ import annotations

from enum import Enum
from typing import List, Optional, Dict, Any, Union
from pydantic import BaseModel, Field


class BlockType(str, Enum):
    HEADING = "heading"
    PARAGRAPH = "paragraph"
    BULLET_LIST = "bullet_list"
    NUMBERED_LIST = "numbered_list"
    TABLE = "table"
    FIGURE = "figure"
    FIGURE_DESCRIPTION = "figure_description"
    CAPTION = "caption"


class SourceType(str, Enum):
    DOCX = "docx"


class BaseBlock(BaseModel):
    id: str
    type: BlockType
    order: int
    text: Optional[str] = None
    page_or_slide: Optional[int] = None
    section_path: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class FigureBlock(BaseBlock):
    image_path: Optional[str] = None
    image_name: Optional[str] = None
    caption: Optional[str] = None
    rel_id: Optional[str] = None
    alt_text: Optional[str] = None


class TableCell(BaseModel):
    row: int
    col: int
    text: str


class TableBlock(BaseBlock):
    rows: int
    cols: int
    cells: List[TableCell] = Field(default_factory=list)
    summary: Optional[str] = None


Block = Union[BaseBlock, FigureBlock, TableBlock]


class Section(BaseModel):
    title: str
    path: List[str]
    blocks: List[Block] = Field(default_factory=list)


class CanonicalDocument(BaseModel):
    document_id: str
    source_type: SourceType
    source_file: str
    title: Optional[str] = None
    language: Optional[str] = None
    sections: List[Section] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)