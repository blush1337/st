from __future__ import annotations

import logging
import os
import threading
from collections.abc import Callable

from pynput import keyboard

log = logging.getLogger(__name__)

MODIFIER_ORDER = ("ctrl", "alt", "shift", "win")
MODIFIER_ALIASES = {
    "control": "ctrl",
    "cmd": "win",
    "super": "win",
    "meta": "win",
}


def normalize_hotkey(value: str) -> str:
    parts = [part.strip().lower() for part in value.split("+") if part.strip()]
    parts = [MODIFIER_ALIASES.get(part, part) for part in parts]
    modifiers = [name for name in MODIFIER_ORDER if name in parts]
    keys = [part for part in parts if part not in MODIFIER_ORDER]
    if len(keys) != 1 or not modifiers:
        raise ValueError("Use at least one modifier and one key")
    key = keys[0]
    if len(key) != 1 and key not in {
        "space", "enter", "tab", "home", "end", "page_up", "page_down",
        "insert", "delete", "f1", "f2", "f3", "f4", "f5", "f6", "f7",
        "f8", "f9", "f10", "f11", "f12",
    }:
        raise ValueError("That key is not supported")
    if len(set(parts)) != len(parts):
        raise ValueError("The shortcut contains a repeated key")
    return "+".join([*modifiers, key])


def display_hotkey(value: str) -> str:
    names = {"ctrl": "Ctrl", "alt": "Alt", "shift": "Shift", "win": "Win"}
    return " + ".join(names.get(part, part.upper()) for part in value.split("+"))


def _pynput_hotkey(value: str) -> str:
    mapped = []
    for part in normalize_hotkey(value).split("+"):
        if part in {"ctrl", "alt", "shift"}:
            mapped.append(f"<{part}>")
        elif part == "win":
            mapped.append("<cmd>")
        elif len(part) > 1:
            mapped.append(f"<{part}>")
        else:
            mapped.append(part)
    return "+".join(mapped)


def hotkey_is_available(value: str) -> bool:
    """Ask Windows whether another application reserved this combination."""
    if os.name != "nt":
        return True
    import ctypes

    parts = normalize_hotkey(value).split("+")
    modifiers = 0x4000  # MOD_NOREPEAT
    modifier_flags = {"alt": 0x0001, "ctrl": 0x0002, "shift": 0x0004, "win": 0x0008}
    for part in parts[:-1]:
        modifiers |= modifier_flags[part]
    key_name = parts[-1]
    special_keys = {
        "space": 0x20,
        "enter": 0x0D,
        "tab": 0x09,
        "home": 0x24,
        "end": 0x23,
        "page_up": 0x21,
        "page_down": 0x22,
        "insert": 0x2D,
        "delete": 0x2E,
    }
    if key_name.startswith("f") and key_name[1:].isdigit():
        virtual_key = 0x70 + int(key_name[1:]) - 1
    elif key_name in special_keys:
        virtual_key = special_keys[key_name]
    else:
        virtual_key = ord(key_name.upper())
    test_id = 0x51A7
    registered = bool(
        ctypes.windll.user32.RegisterHotKey(None, test_id, modifiers, virtual_key)
    )
    if registered:
        ctypes.windll.user32.UnregisterHotKey(None, test_id)
    return registered


class HotkeyManager:
    def __init__(self, callback: Callable[[], None]) -> None:
        self._callback = callback
        self._listener: keyboard.Listener | None = None
        self._hotkey: keyboard.HotKey | None = None

    def register(self, shortcut: str) -> None:
        self.stop()
        parsed = keyboard.HotKey.parse(_pynput_hotkey(shortcut))
        self._hotkey = keyboard.HotKey(parsed, self._callback)
        listener: keyboard.Listener

        def on_press(key: keyboard.Key | keyboard.KeyCode | None) -> None:
            if self._hotkey is not None:
                self._hotkey.press(listener.canonical(key))

        def on_release(key: keyboard.Key | keyboard.KeyCode | None) -> None:
            if self._hotkey is not None:
                self._hotkey.release(listener.canonical(key))

        listener = keyboard.Listener(on_press=on_press, on_release=on_release)
        self._listener = listener
        listener.start()
        log.info("Registered global shortcut %s", display_hotkey(shortcut))

    def stop(self) -> None:
        if self._listener is not None:
            listener = self._listener
            listener.stop()
            if listener is not threading.current_thread():
                listener.join(1)
            self._listener = None
        self._hotkey = None
