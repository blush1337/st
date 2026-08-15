from __future__ import annotations

import logging
import uuid

from PySide6.QtCore import QObject, QRect, QRunnable, QThreadPool, Signal, Slot
from PySide6.QtWidgets import QApplication, QSystemTrayIcon

from .capture import CaptureError, ScreenCapture, Selection
from .config import AppSettings, SettingsStore
from .diagnostics import log_event
from .hotkeys import HotkeyManager
from .models import PipelineResult
from .ocr import OCRError, RapidOCREngine
from .pipeline import NoTextFoundError, TranslationPipeline
from .startup import set_launch_at_startup
from .translation.base import TranslationError
from .translation.service import TranslationService
from .ui.result_overlay import ProcessingPopup, TranslationOverlay
from .ui.selector import SelectionController
from .ui.settings_window import SettingsWindow
from .ui.tray import TrayController

log = logging.getLogger(__name__)


class HotkeyBridge(QObject):
    activated = Signal()


class WorkerSignals(QObject):
    finished = Signal(object)
    failed = Signal(str)


class PipelineWorker(QRunnable):
    def __init__(
        self,
        pipeline: TranslationPipeline,
        selection: Selection,
        settings: AppSettings,
        operation_id: str,
    ) -> None:
        super().__init__()
        # The GUI owns the worker until its queued completion signal is handled.
        self.setAutoDelete(False)
        self.pipeline = pipeline
        self.selection = selection
        self.settings = settings
        self.operation_id = operation_id
        self.signals = WorkerSignals()

    @Slot()
    def run(self) -> None:
        try:
            self.signals.finished.emit(
                self.pipeline.run(self.selection, self.settings, self.operation_id)
            )
        except (CaptureError, OCRError, TranslationError, NoTextFoundError) as exc:
            log.warning("Capture pipeline stopped: %s", exc)
            self.signals.failed.emit(str(exc))
        except Exception:
            log.exception("Unexpected capture pipeline failure")
            self.signals.failed.emit("An unexpected error occurred. See the application log.")


class ScreenTranslatorApplication(QObject):
    def __init__(self, qt_app: QApplication, force_minimized: bool = False) -> None:
        super().__init__()
        self.qt_app = qt_app
        self.store = SettingsStore()
        self.settings = self.store.load()
        self.force_minimized = force_minimized
        self.settings_window: SettingsWindow | None = None
        self.result_overlay: TranslationOverlay | None = None
        self.processing_popup: ProcessingPopup | None = None
        self.selection = SelectionController(
            self._selection_finished, self._selection_cancelled
        )
        self.pipeline = TranslationPipeline(
            ScreenCapture(), RapidOCREngine(), TranslationService()
        )
        self.thread_pool = QThreadPool(self)
        self.thread_pool.setMaxThreadCount(1)
        self.active_workers: dict[str, PipelineWorker] = {}
        self.busy = False
        self.paused = not self.settings.hotkey.enabled

        self.hotkey_bridge = HotkeyBridge()
        self.hotkey_bridge.activated.connect(self.begin_capture)
        self.hotkey = HotkeyManager(self.hotkey_bridge.activated.emit)

        self.tray = TrayController(self.settings.hotkey.shortcut)
        self.tray.captureRequested.connect(self.begin_capture)
        self.tray.settingsRequested.connect(self.show_settings)
        self.tray.pauseChanged.connect(self.set_paused)
        self.tray.exitRequested.connect(self.shutdown)
        self.tray.set_paused(self.paused)
        log_event(
            log,
            "startup",
            "settings_loaded",
            hotkey=self.settings.hotkey.shortcut,
            hotkey_enabled=self.settings.hotkey.enabled,
            translation_provider=self.settings.translation.provider,
            source_language=self.settings.translation.source_language,
            target_language=self.settings.translation.target_language,
            ocr_engine=self.settings.ocr.engine,
        )

    def start(self) -> None:
        log_event(
            log,
            "startup",
            "ui_starting",
            force_minimized=self.force_minimized,
            configured_start_minimized=self.settings.general.start_minimized,
            tray_available=QSystemTrayIcon.isSystemTrayAvailable(),
        )
        self.tray.show()
        if not self.paused:
            self._register_hotkey()
        minimized = self.force_minimized or self.settings.general.start_minimized
        if not minimized:
            self.show_settings()
        elif self.settings.general.tray_notifications:
            self.tray.message(
                "Screen Region Translator",
                "Running in the notification area. Use the capture shortcut to translate a region.",
            )
        log_event(log, "startup", "ready", minimized=minimized, paused=self.paused)

    def _register_hotkey(self) -> None:
        log_event(
            log,
            "hotkey",
            "registration_started",
            shortcut=self.settings.hotkey.shortcut,
        )
        try:
            self.hotkey.register(self.settings.hotkey.shortcut)
            log_event(
                log,
                "hotkey",
                "registration_completed",
                shortcut=self.settings.hotkey.shortcut,
            )
        except Exception:
            log.exception("Global hotkey registration failed")
            self.paused = True
            self.tray.set_paused(True)
            self.tray.message(
                "Shortcut unavailable",
                "The global shortcut could not be registered. Choose another shortcut in Settings.",
                error=True,
            )
            log_event(
                log,
                "hotkey",
                "registration_failed",
                level=logging.ERROR,
                shortcut=self.settings.hotkey.shortcut,
            )

    @Slot()
    def begin_capture(self) -> None:
        log_event(
            log,
            "selection",
            "requested",
            paused=self.paused,
            busy=self.busy,
        )
        if self.paused:
            log_event(log, "selection", "ignored", reason="hotkey_paused")
            return
        if self.busy:
            if self.settings.general.tray_notifications:
                self.tray.message("Already working", "Wait for the current translation to finish.")
            log_event(log, "selection", "ignored", reason="pipeline_busy")
            return
        if self.result_overlay is not None:
            self.result_overlay.close()
            self.result_overlay = None
        self.selection.start()
        log_event(
            log,
            "selection",
            "overlay_shown",
            screens=len(self.selection.windows),
        )

    def _selection_cancelled(self) -> None:
        log_event(log, "selection", "cancelled")

    def _selection_finished(self, selection: Selection) -> None:
        operation_id = uuid.uuid4().hex[:8]
        log_event(
            log,
            "selection",
            "confirmed",
            operation_id=operation_id,
            screen_index=selection.screen_index,
            logical_x=selection.x,
            logical_y=selection.y,
            logical_width=selection.width,
            logical_height=selection.height,
            global_x=selection.global_x,
            global_y=selection.global_y,
            device_pixel_ratio=selection.device_pixel_ratio,
        )
        self.busy = True
        region = QRect(
            selection.global_x,
            selection.global_y,
            selection.global_width,
            selection.global_height,
        )
        self.processing_popup = ProcessingPopup(region)
        self.processing_popup.show()
        log_event(
            log,
            "processing_indicator",
            "shown",
            level=logging.DEBUG,
            operation_id=operation_id,
        )
        worker = PipelineWorker(
            self.pipeline, selection, self.settings, operation_id
        )
        worker.signals.finished.connect(
            lambda result, area=region, op=operation_id: self._pipeline_finished(
                op, result, area
            )
        )
        worker.signals.failed.connect(
            lambda message, area=region, op=operation_id: self._pipeline_failed(
                op, message, area
            )
        )
        self.active_workers[operation_id] = worker
        self.thread_pool.start(worker)
        log_event(
            log,
            "pipeline",
            "queued",
            operation_id=operation_id,
            active_threads=self.thread_pool.activeThreadCount(),
        )

    def _clear_processing(self) -> None:
        self.busy = False
        if self.processing_popup is not None:
            self.processing_popup.close()
            self.processing_popup.deleteLater()
            self.processing_popup = None
            log_event(
                log,
                "processing_indicator",
                "closed",
                level=logging.DEBUG,
            )

    def _pipeline_finished(
        self, operation_id: str, result: PipelineResult, region: QRect
    ) -> None:
        # Keep the signal owner alive until this queued GUI callback returns.
        completed_worker = self.active_workers.pop(operation_id, None)
        self._clear_processing()
        log_event(
            log,
            "overlay",
            "result_showing",
            operation_id=operation_id,
            ocr_items=len(result.items),
            original_characters=len(result.original_text),
            translated_characters=len(result.translated_text),
            region_x=region.x(),
            region_y=region.y(),
        )
        self.result_overlay = TranslationOverlay(result, region, self.settings.overlay)
        self.result_overlay.closed.connect(self._overlay_closed)
        self.result_overlay.show()
        log_event(
            log,
            "overlay",
            "result_shown",
            operation_id=operation_id,
            panel_width=self.result_overlay.width(),
            panel_height=self.result_overlay.height(),
        )
        del completed_worker

    def _pipeline_failed(
        self, operation_id: str, message: str, region: QRect
    ) -> None:
        # Keep the signal owner alive until this queued GUI callback returns.
        completed_worker = self.active_workers.pop(operation_id, None)
        self._clear_processing()
        log_event(
            log,
            "overlay",
            "error_showing",
            level=logging.ERROR,
            operation_id=operation_id,
            message=message,
        )
        result = PipelineResult("", f"Couldn’t translate this area.\n{message}", ())
        error_settings = self.settings.overlay
        self.result_overlay = TranslationOverlay(result, region, error_settings)
        self.result_overlay.closed.connect(self._overlay_closed)
        self.result_overlay.show()
        del completed_worker

    def _overlay_closed(self) -> None:
        log_event(log, "overlay", "closed")
        self.result_overlay = None

    @Slot()
    def show_settings(self) -> None:
        log_event(log, "settings", "window_requested")
        if self.settings_window is None:
            self.settings_window = SettingsWindow(self.settings)
            self.settings_window.saved.connect(self.apply_settings)
            self.settings_window.exitRequested.connect(self.shutdown)
            self.settings_window.finished.connect(self._settings_closed)
        else:
            self.settings_window.load(self.settings)
        self.settings_window.show()
        self.settings_window.raise_()
        self.settings_window.activateWindow()

    def _settings_closed(self) -> None:
        log_event(log, "settings", "window_closed")
        if self.settings_window is not None:
            self.settings_window.deleteLater()
            self.settings_window = None

    @Slot(object)
    def apply_settings(self, settings: AppSettings) -> None:
        old_startup = self.settings.general.launch_at_startup
        self.settings = settings
        try:
            self.store.save(settings)
            if old_startup != settings.general.launch_at_startup:
                set_launch_at_startup(settings.general.launch_at_startup)
        except OSError:
            log.exception("Could not save settings")
            self.tray.message(
                "Settings not saved",
                "Windows could not save the settings file.",
                error=True,
            )
            return
        log_event(
            log,
            "settings",
            "saved",
            hotkey=settings.hotkey.shortcut,
            translation_provider=settings.translation.provider,
            source_language=settings.translation.source_language,
            target_language=settings.translation.target_language,
            ocr_engine=settings.ocr.engine,
            startup=settings.general.launch_at_startup,
        )
        self.tray.update_hotkey(settings.hotkey.shortcut)
        if not self.paused:
            self._register_hotkey()

    @Slot(bool)
    def set_paused(self, paused: bool) -> None:
        log_event(log, "hotkey", "pause_changed", paused=paused)
        self.paused = paused
        self.settings.hotkey.enabled = not paused
        self.tray.set_paused(paused)
        if paused:
            self.hotkey.stop()
            self.selection.close()
        else:
            self._register_hotkey()
        try:
            self.store.save(self.settings)
        except OSError:
            log.exception("Could not persist paused state")

    @Slot()
    def shutdown(self) -> None:
        log_event(
            log,
            "shutdown",
            "requested",
            busy=self.busy,
            active_threads=self.thread_pool.activeThreadCount(),
        )
        self.selection.close()
        self.hotkey.stop()
        self.thread_pool.clear()
        self.thread_pool.waitForDone(20_000)
        self.active_workers.clear()
        if self.processing_popup is not None:
            self.processing_popup.close()
        if self.result_overlay is not None:
            self.result_overlay.close()
        self.tray.hide()
        log_event(log, "shutdown", "completed")
        self.qt_app.quit()
