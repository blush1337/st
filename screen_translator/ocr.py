from __future__ import annotations

import logging
import threading
from typing import Any

import numpy as np
from PIL import Image, ImageOps

from .config import OCRSettings
from .diagnostics import log_event
from .models import BoundingBox, OCRResult

log = logging.getLogger(__name__)


class OCRError(RuntimeError):
    """An OCR failure safe to summarize in the UI."""


class RapidOCREngine:
    def __init__(self) -> None:
        self._engine: Any = None
        self._lock = threading.Lock()

    def _get_engine(self) -> Any:
        with self._lock:
            if self._engine is None:
                try:
                    from rapidocr_onnxruntime import RapidOCR

                    log.info("Initializing RapidOCR")
                    self._engine = RapidOCR()
                    log.info("RapidOCR initialized")
                except Exception as exc:
                    log.exception("RapidOCR initialization failed")
                    raise OCRError(
                        "Text recognition could not be initialized. Check the log for details."
                    ) from exc
            return self._engine

    @staticmethod
    def _prepare(image: Image.Image, enabled: bool) -> Image.Image:
        image = image.convert("RGB")
        if not enabled:
            return image
        grayscale = ImageOps.grayscale(image)
        return ImageOps.autocontrast(grayscale, cutoff=1).convert("RGB")

    def recognize(self, image: Image.Image, settings: OCRSettings) -> list[OCRResult]:
        try:
            prepared = self._prepare(image, settings.preprocess)
            log_event(
                log,
                "ocr",
                "input_prepared",
                level=logging.DEBUG,
                width=prepared.width,
                height=prepared.height,
                preprocessing=settings.preprocess,
            )
            raw, elapsed = self._get_engine()(np.asarray(prepared))
            if not raw:
                log_event(log, "ocr", "engine_returned_empty", engine_elapsed=elapsed)
                return []
            results: list[OCRResult] = []
            for line in raw:
                box, text, confidence = line
                score = float(confidence)
                if score < settings.confidence_threshold or not str(text).strip():
                    continue
                points = tuple((int(round(x)), int(round(y))) for x, y in box)
                if len(points) != 4:
                    continue
                results.append(
                    OCRResult(
                        text=str(text).strip(),
                        confidence=score,
                        bounding_box=points,  # type: ignore[arg-type]
                    )
                )
            log_event(
                log,
                "ocr",
                "engine_results_filtered",
                level=logging.DEBUG,
                raw_items=len(raw),
                accepted_items=len(results),
                rejected_items=len(raw) - len(results),
                engine_elapsed=elapsed,
            )
            return results
        except OCRError:
            raise
        except Exception as exc:
            log.exception("OCR failed")
            raise OCRError("Text recognition failed for this capture.") from exc
