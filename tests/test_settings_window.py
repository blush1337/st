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

