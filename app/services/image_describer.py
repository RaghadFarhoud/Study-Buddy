from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path


class ImageDescriber(ABC):
    @abstractmethod
    def describe(
    self,
    image_path: Path,
    context_text: str | None = None,
    caption: str | None = None,
    alt_text: str | None = None,
) -> str:
        raise NotImplementedError