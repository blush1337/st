from __future__ import annotations

from PIL import Image

from screen_translator.config import OCRSettings
from screen_translator.ocr import RapidOCREngine


class FakeRapidOCR:
    def __call__(self, _image):
        return (
            [
                [[[1, 2], [40, 2], [40, 18], [1, 18]], "Settings", 0.97],
                [[[1, 20], [30, 20], [30, 36], [1, 36]], "noise", 0.2],
            ],
            0.01,
        )


def test_ocr_returns_structured_filtered_results() -> None:
    engine = RapidOCREngine()
    engine._engine = FakeRapidOCR()

    results = engine.recognize(Image.new("RGB", (60, 40), "white"), OCRSettings())

    assert len(results) == 1
    assert results[0].text == "Settings"
    assert results[0].confidence == 0.97
    assert results[0].bounding_box[2] == (40, 18)

