from __future__ import annotations

import pytest

from screen_translator.hotkeys import display_hotkey, normalize_hotkey


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("Shift + Control + T", "ctrl+shift+t"),
        ("Alt+Q", "alt+q"),
        ("meta + ctrl + s", "ctrl+win+s"),
        ("ctrl+F12", "ctrl+f12"),
    ],
)
def test_normalize_hotkey(raw: str, expected: str) -> None:
    assert normalize_hotkey(raw) == expected


@pytest.mark.parametrize("raw", ["t", "ctrl+shift", "ctrl+a+b", "ctrl+ctrl+t"])
def test_reject_invalid_hotkeys(raw: str) -> None:
    with pytest.raises(ValueError):
        normalize_hotkey(raw)


def test_display_hotkey() -> None:
    assert display_hotkey("ctrl+alt+s") == "Ctrl + Alt + S"

