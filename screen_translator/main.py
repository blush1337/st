from __future__ import annotations

import argparse
import ctypes
import logging
import os
import sys

from PySide6.QtCore import QLockFile, QStandardPaths
from PySide6.QtGui import QFont
from PySide6.QtWidgets import QApplication, QMessageBox

from .app import ScreenTranslatorApplication
from .logging_setup import configure_logging

log = logging.getLogger(__name__)


def enable_dpi_awareness() -> None:
    if os.name != "nt":
        return
    try:
        # PER_MONITOR_AWARE_V2 keeps Qt screen geometry and physical capture aligned.
        ctypes.windll.user32.SetProcessDpiAwarenessContext(ctypes.c_void_p(-4))
    except (AttributeError, OSError):
        try:
            ctypes.windll.shcore.SetProcessDpiAwareness(2)
        except (AttributeError, OSError):
            pass


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Translate text in a screen region")
    parser.add_argument("--minimized", action="store_true", help="start in the notification area")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    enable_dpi_awareness()
    configure_logging()
    app = QApplication(sys.argv[:1])
    app.setApplicationName("Screen Region Translator")
    app.setOrganizationName("Screen Region Translator")
    app.setQuitOnLastWindowClosed(False)
    app.setFont(QFont("Segoe UI", 9))

    lock_path = QStandardPaths.writableLocation(QStandardPaths.StandardLocation.TempLocation)
    instance_lock = QLockFile(os.path.join(lock_path, "screen-region-translator.lock"))
    instance_lock.setStaleLockTime(0)
    if not instance_lock.tryLock(100):
        QMessageBox.information(
            None,
            "Screen Region Translator",
            "Screen Region Translator is already running in the notification area.",
        )
        return 0

    controller = ScreenTranslatorApplication(app, force_minimized=args.minimized)
    app.aboutToQuit.connect(controller.hotkey.stop)
    controller.start()
    log.info("Application started")
    exit_code = app.exec()
    logging.shutdown()
    return exit_code
