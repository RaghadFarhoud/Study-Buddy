from __future__ import annotations

from enum import Enum
from typing import List, Optional, Dict, Any, Union, Literal
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
    PPTX = "pptx"


class ListItem(BaseModel):
    text: str
    level: int = 0


class TableCell(BaseModel):
    row: int
    col: int
    text: str


class BaseBlock(BaseModel):
    id: str
    type: BlockType
    order: int
    page_or_slide: Optional[int] = None
    section_path: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class HeadingBlock(BaseBlock):
    type: Literal[BlockType.HEADING] = BlockType.HEADING
    text: str
    level: int = 1


class ParagraphBlock(BaseBlock):
    type: Literal[BlockType.PARAGRAPH] = BlockType.PARAGRAPH
    text: str


class BulletListBlock(BaseBlock):
    type: Literal[BlockType.BULLET_LIST] = BlockType.BULLET_LIST
    items: List[ListItem] = Field(default_factory=list)


class NumberedListBlock(BaseBlock):
    type: Literal[BlockType.NUMBERED_LIST] = BlockType.NUMBERED_LIST
    items: List[ListItem] = Field(default_factory=list)


class FigureBlock(BaseBlock):
    type: Literal[BlockType.FIGURE] = BlockType.FIGURE
    text: Optional[str] = None
    image_path: Optional[str] = None
    image_name: Optional[str] = None
    caption: Optional[str] = None
    rel_id: Optional[str] = None
    alt_text: Optional[str] = None


class TableBlock(BaseBlock):
    type: Literal[BlockType.TABLE] = BlockType.TABLE
    text: Optional[str] = None
    rows: int
    cols: int
    cells: List[TableCell] = Field(default_factory=list)
    summary: Optional[str] = None
    
class CaptionBlock(BaseBlock):
    type: Literal[BlockType.CAPTION] = BlockType.CAPTION
    text: str
    figure_ref_id: Optional[str] = None


class FigureDescriptionBlock(BaseBlock):
    type: Literal[BlockType.FIGURE_DESCRIPTION] = BlockType.FIGURE_DESCRIPTION
    text: str
    figure_ref_id: Optional[str] = None
    generated_by: Optional[str] = None

Block = Union[
    BaseBlock,
    HeadingBlock,
    ParagraphBlock,
    BulletListBlock,
    NumberedListBlock,
    FigureBlock,
    CaptionBlock,
    FigureDescriptionBlock,
    TableBlock,
]


class Section(BaseModel):
    title: Optional[str] = None
    path: List[str] = Field(default_factory=list)
    blocks: List[Block] = Field(default_factory=list)
    page_or_slide: Optional[int] = None
    notes: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class CanonicalDocument(BaseModel):
    document_id: str
    source_type: SourceType
    source_file: str
    title: Optional[str] = None
    language: Optional[str] = None
    sections: List[Section] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)

