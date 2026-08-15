from __future__ import annotations

from dataclasses import dataclass

from .capture import ScreenCapture, Selection
from .config import AppSettings
from .models import PipelineResult
from .ocr import RapidOCREngine
from .translation import TranslationService


class NoTextFoundError(RuntimeError):
    pass


@dataclass(slots=True)
class TranslationPipeline:
    capture: ScreenCapture
    ocr: RapidOCREngine
    translation: TranslationService

    def run(self, selection: Selection, settings: AppSettings) -> PipelineResult:
        image = self.capture.capture(selection)
        items = self.ocr.recognize(image, settings.ocr)
        if not items:
            raise NoTextFoundError("No readable text was found in that area.")
        original = "\n".join(item.text for item in items)
        translated = self.translation.translate(original, settings.translation)
        return PipelineResult(original, translated, tuple(items))
