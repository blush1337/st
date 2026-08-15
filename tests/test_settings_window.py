from __future__ import annotations

from screen_translator.config import AppSettings
from screen_translator.ui.settings_window import SettingsWindow


def test_settings_window_round_trip(qapp) -> None:
    settings = AppSettings()
    settings.hotkey.shortcut = "alt+q"
    settings.overlay.position = "above"
    window = SettingsWindow(settings)

    collected = window.collect()

    assert collected.hotkey.shortcut == "alt+q"
    assert collected.overlay.position == "above"
    assert window.navigation.count() == 4
    window.close()


def test_close_and_cancel_hide_settings_to_tray(qapp) -> None:
    window = SettingsWindow(AppSettings())
    hidden_events: list[bool] = []
    window.hiddenToTray.connect(lambda: hidden_events.append(True))
    window.show()
    qapp.processEvents()

    window.close()
    qapp.processEvents()

    assert not window.isVisible()
    assert hidden_events == [True]

    window.show()
    qapp.processEvents()
    window.reject()
    qapp.processEvents()

    assert not window.isVisible()
    assert hidden_events == [True, True]
    window.deleteLater()
