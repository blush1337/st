from __future__ import annotations

from dataclasses import dataclass


Point = tuple[int, int]
BoundingBox = tuple[Point, Point, Point, Point]


@dataclass(frozen=True, slots=True)
class OCRResult:
    text: str
    confidence: float
    bounding_box: BoundingBox


@dataclass(frozen=True, slots=True)
class PipelineResult:
    original_text: str
    translated_text: str
    items: tuple[OCRResult, ...]

