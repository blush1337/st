from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass

from .capture import ScreenCapture, Selection
from .config import AppSettings
from .diagnostics import logged_stage, log_event
from .models import PipelineResult
from .ocr import RapidOCREngine
from .translation import TranslationService


class NoTextFoundError(RuntimeError):
    pass


log = logging.getLogger(__name__)


@dataclass(slots=True)
class TranslationPipeline:
    capture: ScreenCapture
    ocr: RapidOCREngine
    translation: TranslationService

    def run(
        self,
        selection: Selection,
        settings: AppSettings,
        operation_id: str | None = None,
    ) -> PipelineResult:
        operation_id = operation_id or uuid.uuid4().hex[:8]
        with logged_stage(log, "pipeline", operation_id=operation_id):
            with logged_stage(
                log,
                "capture",
                operation_id=operation_id,
                screen_index=selection.screen_index,
                logical_width=selection.width,
                logical_height=selection.height,
                device_pixel_ratio=selection.device_pixel_ratio,
            ):
                image = self.capture.capture(selection)
            log_event(
                log,
                "capture",
                "image_ready",
                level=logging.DEBUG,
                operation_id=operation_id,
                physical_width=image.width,
                physical_height=image.height,
            )

            with logged_stage(
                log,
                "ocr",
                operation_id=operation_id,
                engine=settings.ocr.engine,
                model_language=settings.ocr.language,
                preprocessing=settings.ocr.preprocess,
                confidence_threshold=settings.ocr.confidence_threshold,
            ):
                items = self.ocr.recognize(image, settings.ocr)
            log_event(
                log,
                "ocr",
                "results_ready",
                operation_id=operation_id,
                accepted_items=len(items),
            )
            if not items:
                raise NoTextFoundError("No readable text was found in that area.")

            original = "\n".join(item.text for item in items)
            with logged_stage(
                log,
                "translation",
                operation_id=operation_id,
                provider=settings.translation.provider,
                source_language=settings.translation.source_language,
                target_language=settings.translation.target_language,
                input_characters=len(original),
            ):
                translated = self.translation.translate(original, settings.translation)
            log_event(
                log,
                "translation",
                "result_ready",
                level=logging.DEBUG,
                operation_id=operation_id,
                output_characters=len(translated),
            )
            return PipelineResult(original, translated, tuple(items))
