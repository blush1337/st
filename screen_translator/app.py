from __future__ import annotations

import logging

from PySide6.QtCore import QObject, QRect, QRunnable, QThreadPool, Signal, Slot
from PySide6.QtWidgets import QApplication, QSystemTrayIcon

from .capture import CaptureError, ScreenCapture, Selection
from .config import AppSettings, SettingsStore
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
    ) -> None:
        super().__init__()
        self.pipeline = pipeline
        self.selection = selection
        self.settings = settings
        self.signals = WorkerSignals()

    @Slot()
    def run(self) -> None:
        try:
            self.signals.finished.emit(self.pipeline.run(self.selection, self.settings))
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
        self.selection = SelectionController(self._selection_finished, lambda: None)
        self.pipeline = TranslationPipeline(
            ScreenCapture(), RapidOCREngine(), TranslationService()
        )
        self.thread_pool = QThreadPool(self)
        self.thread_pool.setMaxThreadCount(1)
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

    def start(self) -> None:
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

    def _register_hotkey(self) -> None:
        try:
            self.hotkey.register(self.settings.hotkey.shortcut)
        except Exception:
            log.exception("Global hotkey registration failed")
            self.paused = True
            self.tray.set_paused(True)
            self.tray.message(
                "Shortcut unavailable",
                "The global shortcut could not be registered. Choose another shortcut in Settings.",
                error=True,
            )

    @Slot()
    def begin_capture(self) -> None:
        if self.paused:
            return
        if self.busy:
            if self.settings.general.tray_notifications:
                self.tray.message("Already working", "Wait for the current translation to finish.")
            return
        if self.result_overlay is not None:
            self.result_overlay.close()
            self.result_overlay = None
        self.selection.start()

    def _selection_finished(self, selection: Selection) -> None:
        self.busy = True
        region = QRect(
            selection.global_x,
            selection.global_y,
            selection.global_width,
            selection.global_height,
        )
        self.processing_popup = ProcessingPopup(region)
        self.processing_popup.show()
        worker = PipelineWorker(self.pipeline, selection, self.settings)
        worker.signals.finished.connect(
            lambda result, area=region: self._pipeline_finished(result, area)
        )
        worker.signals.failed.connect(
            lambda message, area=region: self._pipeline_failed(message, area)
        )
        self.thread_pool.start(worker)

    def _clear_processing(self) -> None:
        self.busy = False
        if self.processing_popup is not None:
            self.processing_popup.close()
            self.processing_popup.deleteLater()
            self.processing_popup = None

    def _pipeline_finished(self, result: PipelineResult, region: QRect) -> None:
        self._clear_processing()
        self.result_overlay = TranslationOverlay(result, region, self.settings.overlay)
        self.result_overlay.show()

    def _pipeline_failed(self, message: str, region: QRect) -> None:
        self._clear_processing()
        result = PipelineResult("", f"Couldn’t translate this area.\n{message}", ())
        error_settings = self.settings.overlay
        self.result_overlay = TranslationOverlay(result, region, error_settings)
        self.result_overlay.show()

    @Slot()
    def show_settings(self) -> None:
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
        self.tray.update_hotkey(settings.hotkey.shortcut)
        if not self.paused:
            self._register_hotkey()

    @Slot(bool)
    def set_paused(self, paused: bool) -> None:
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
        log.info("Application shutdown requested")
        self.selection.close()
        self.hotkey.stop()
        self.thread_pool.clear()
        self.thread_pool.waitForDone(20_000)
        if self.processing_popup is not None:
            self.processing_popup.close()
        if self.result_overlay is not None:
            self.result_overlay.close()
        self.tray.hide()
        self.qt_app.quit()
