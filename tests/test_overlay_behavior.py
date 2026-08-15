from __future__ import annotations

from PySide6.QtCore import QEvent, QRect, Qt
from PySide6.QtGui import QKeyEvent
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication, QPushButton

from screen_translator.config import OverlaySettings
from screen_translator.models import PipelineResult
from screen_translator.ui.result_overlay import TranslationOverlay


def _overlay() -> TranslationOverlay:
    settings = OverlaySettings(auto_dismiss=True, dismiss_seconds=2)
    return TranslationOverlay(
        PipelineResult("Original", "Translated", ()),
        QRect(100, 100, 200, 80),
        settings,
    )


def test_overlay_survives_focus_loss_even_with_old_auto_dismiss_setting(qapp) -> None:
    overlay = _overlay()
    overlay.show()
    qapp.processEvents()

    QApplication.sendEvent(overlay, QEvent(QEvent.Type.WindowDeactivate))
    qapp.processEvents()

    assert overlay.isVisible()
    window_type = overlay.windowFlags() & Qt.WindowType.WindowType_Mask
    assert window_type == Qt.WindowType.Tool
    overlay.close()


def test_escape_closes_overlay(qapp) -> None:
    overlay = _overlay()
    overlay.show()
    qapp.processEvents()

    QApplication.sendEvent(
        overlay,
        QKeyEvent(QEvent.Type.KeyPress, Qt.Key.Key_Escape, Qt.KeyboardModifier.NoModifier),
    )
    QTest.qWait(180)

    assert not overlay.isVisible()


def test_close_button_closes_overlay(qapp) -> None:
    overlay = _overlay()
    overlay.show()
    qapp.processEvents()
    close_button = next(
        button
        for button in overlay.findChildren(QPushButton)
        if button.text() == "Close"
    )

    close_button.click()
    QTest.qWait(180)

    assert not overlay.isVisible()
