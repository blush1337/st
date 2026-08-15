from __future__ import annotations

from PySide6.QtCore import QEventLoop, QTimer
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QPushButton

from screen_translator.app import ScreenTranslatorApplication
from screen_translator.capture import Selection
from screen_translator.models import PipelineResult


class ImmediatePipeline:
    def run(self, _selection, _settings, _operation_id):
        return PipelineResult("Original", "Translated", ())


def test_worker_completion_reaches_gui_and_replaces_processing_popup(
    qapp, tmp_path, monkeypatch
) -> None:
    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path))
    controller = ScreenTranslatorApplication(qapp, force_minimized=True)
    controller.pipeline = ImmediatePipeline()
    selection = Selection(0, 10, 10, 120, 50, 1.0, 10, 10, 120, 50)

    loop = QEventLoop()
    poll = QTimer()
    poll.setInterval(10)
    poll.timeout.connect(lambda: loop.quit() if not controller.busy else None)
    poll.start()
    QTimer.singleShot(2_000, loop.quit)

    controller._selection_finished(selection)
    loop.exec()

    assert controller.busy is False
    assert controller.processing_popup is None
    assert controller.result_overlay is not None
    assert controller.result_overlay.text.toPlainText() == "Translated"
    assert controller.active_workers == {}

    poll.stop()
    close_button = next(
        button
        for button in controller.result_overlay.findChildren(QPushButton)
        if button.text() == "Close"
    )
    close_button.click()
    QTest.qWait(200)

    assert controller.result_overlay is None
    assert qapp.closingDown() is False

    controller.thread_pool.waitForDone()
    controller.tray.hide()
