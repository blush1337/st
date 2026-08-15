from __future__ import annotations

from screen_translator.ui.tray import TrayController


def test_tray_has_explicit_close_program_action(qapp) -> None:
    tray = TrayController("ctrl+shift+t")
    exit_events: list[bool] = []
    tray.exitRequested.connect(lambda: exit_events.append(True))

    assert tray.exit_action.text() == "Close Program"
    tray.exit_action.trigger()

    assert exit_events == [True]
    tray.hide()
