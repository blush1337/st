from __future__ import annotations

import json

from screen_translator.config import AppSettings, SettingsStore


def test_settings_round_trip(tmp_path) -> None:
    path = tmp_path / "settings.json"
    settings = AppSettings()
    settings.hotkey.shortcut = "alt+q"
    settings.translation.target_language = "de"
    SettingsStore(path).save(settings)

    loaded = SettingsStore(path).load()

    assert loaded.hotkey.shortcut == "alt+q"
    assert loaded.translation.target_language == "de"
    assert not path.with_suffix(".tmp").exists()


def test_settings_ignore_unknown_keys_and_keep_defaults(tmp_path) -> None:
    path = tmp_path / "settings.json"
    path.write_text(
        json.dumps({"general": {"start_minimized": True, "future_key": 1}}),
        encoding="utf-8",
    )

    loaded = SettingsStore(path).load()

    assert loaded.general.start_minimized is True
    assert loaded.general.minimize_to_tray is True
    assert loaded.hotkey.shortcut == "ctrl+shift+t"


def test_invalid_settings_fall_back_to_defaults(tmp_path) -> None:
    path = tmp_path / "settings.json"
    path.write_text("not json", encoding="utf-8")

    assert SettingsStore(path).load() == AppSettings()

