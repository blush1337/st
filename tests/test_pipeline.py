from __future__ import annotations

import pytest
from PIL import Image

from screen_translator.capture import Selection
from screen_translator.config import AppSettings
from screen_translator.models import OCRResult
from screen_translator.pipeline import NoTextFoundError, TranslationPipeline


SELECTION = Selection(0, 0, 0, 100, 40, 1.0, 0, 0, 100, 40)


class FakeCapture:
    def capture(self, _selection):
        return Image.new("RGB", (100, 40), "white")


class FakeOCR:
    def __init__(self, results):
        self.results = results

    def recognize(self, _image, _settings):
        return self.results


class FakeTranslation:
    def translate(self, text, _settings):
        return f"translated: {text}"


def test_pipeline_preserves_ocr_items() -> None:
    item = OCRResult("Settings", 0.9, ((0, 0), (50, 0), (50, 20), (0, 20)))
    pipeline = TranslationPipeline(FakeCapture(), FakeOCR([item]), FakeTranslation())

    result = pipeline.run(SELECTION, AppSettings())

    assert result.original_text == "Settings"
    assert result.translated_text == "translated: Settings"
    assert result.items == (item,)


def test_pipeline_reports_no_text() -> None:
    pipeline = TranslationPipeline(FakeCapture(), FakeOCR([]), FakeTranslation())

    with pytest.raises(NoTextFoundError):
        pipeline.run(SELECTION, AppSettings())

