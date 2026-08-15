from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFocusEvent, QKeyEvent
from PySide6.QtWidgets import QLineEdit

from ..hotkeys import display_hotkey, normalize_hotkey


class HotkeyEdit(QLineEdit):
    shortcutChanged = Signal(str)

    def __init__(self) -> None:
        super().__init__()
        self._shortcut = "ctrl+shift+t"
        self.setReadOnly(True)
        self.setClearButtonEnabled(False)
        self.setToolTip("Click, then press a modifier and one key")
        self.setShortcut(self._shortcut)

    def shortcut(self) -> str:
        return self._shortcut

    def setShortcut(self, value: str) -> None:
        self._shortcut = normalize_hotkey(value)
        self.setText(display_hotkey(self._shortcut))

    def focusInEvent(self, event: QFocusEvent) -> None:
        super().focusInEvent(event)
        self.setText("Press shortcut…")
        self.selectAll()

    def focusOutEvent(self, event: QFocusEvent) -> None:
        self.setText(display_hotkey(self._shortcut))
        super().focusOutEvent(event)

    def keyPressEvent(self, event: QKeyEvent) -> None:
        if event.key() in {
            Qt.Key.Key_Control,
            Qt.Key.Key_Shift,
            Qt.Key.Key_Alt,
            Qt.Key.Key_Meta,
        }:
            return
        modifiers: list[str] = []
        active = event.modifiers()
        if active & Qt.KeyboardModifier.ControlModifier:
            modifiers.append("ctrl")
        if active & Qt.KeyboardModifier.AltModifier:
            modifiers.append("alt")
        if active & Qt.KeyboardModifier.ShiftModifier:
            modifiers.append("shift")
        if active & Qt.KeyboardModifier.MetaModifier:
            modifiers.append("win")
        if not modifiers:
            self.setText("Add Ctrl, Alt, Shift, or Win")
            return
        key = event.key()
        supported_special = {
            Qt.Key.Key_Space: "space",
            Qt.Key.Key_Return: "enter",
            Qt.Key.Key_Enter: "enter",
            Qt.Key.Key_Tab: "tab",
            Qt.Key.Key_Home: "home",
            Qt.Key.Key_End: "end",
            Qt.Key.Key_PageUp: "page_up",
            Qt.Key.Key_PageDown: "page_down",
            Qt.Key.Key_Insert: "insert",
            Qt.Key.Key_Delete: "delete",
        }
        if Qt.Key.Key_F1 <= key <= Qt.Key.Key_F12:
            key_name = f"f{key - Qt.Key.Key_F1 + 1}"
        else:
            key_name = supported_special.get(key, event.text().lower())
        is_function_key = key_name.startswith("f") and key_name[1:].isdigit()
        if not key_name or not (
            len(key_name) == 1
            or key_name in supported_special.values()
            or is_function_key
        ):
            self.setText("That key is not supported")
            return
        try:
            value = normalize_hotkey("+".join([*modifiers, key_name]))
        except ValueError as exc:
            self.setText(str(exc))
            return
        self.setShortcut(value)
        self.shortcutChanged.emit(value)
        self.clearFocus()
