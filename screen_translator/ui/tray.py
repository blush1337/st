from __future__ import annotations

from PySide6.QtCore import QObject, Signal
from PySide6.QtGui import QAction, QIcon
from PySide6.QtWidgets import QApplication, QMenu, QStyle, QSystemTrayIcon

from ..hotkeys import display_hotkey


class TrayController(QObject):
    captureRequested = Signal()
    settingsRequested = Signal()
    pauseChanged = Signal(bool)
    exitRequested = Signal()

    def __init__(self, hotkey: str) -> None:
        super().__init__()
        style = QApplication.style()
        self.active_icon: QIcon = style.standardIcon(QStyle.StandardPixmap.SP_ComputerIcon)
        self.paused_icon: QIcon = style.standardIcon(QStyle.StandardPixmap.SP_MessageBoxWarning)
        self.tray = QSystemTrayIcon(self.active_icon)
        self.tray.setToolTip(f"Screen Region Translator — {display_hotkey(hotkey)}")
        menu = QMenu()
        self.capture_action = QAction("Translate Region")
        self.capture_action.triggered.connect(self.captureRequested)
        self.settings_action = QAction("Settings")
        self.settings_action.triggered.connect(self.settingsRequested)
        self.pause_action = QAction("Pause Hotkey")
        self.pause_action.setCheckable(True)
        self.pause_action.toggled.connect(self.pauseChanged)
        exit_action = QAction("Exit")
        exit_action.triggered.connect(self.exitRequested)
        menu.addAction(self.capture_action)
        menu.addAction(self.settings_action)
        menu.addSeparator()
        menu.addAction(self.pause_action)
        menu.addSeparator()
        menu.addAction(exit_action)
        self.tray.setContextMenu(menu)
        self.tray.activated.connect(self._activated)

    def show(self) -> None:
        self.tray.show()

    def hide(self) -> None:
        self.tray.hide()

    def update_hotkey(self, hotkey: str) -> None:
        self.tray.setToolTip(f"Screen Region Translator — {display_hotkey(hotkey)}")

    def set_paused(self, paused: bool) -> None:
        self.pause_action.blockSignals(True)
        self.pause_action.setChecked(paused)
        self.pause_action.blockSignals(False)
        self.tray.setIcon(self.paused_icon if paused else self.active_icon)
        self.capture_action.setEnabled(not paused)

    def message(self, title: str, text: str, error: bool = False) -> None:
        icon = (
            QSystemTrayIcon.MessageIcon.Critical
            if error
            else QSystemTrayIcon.MessageIcon.Information
        )
        self.tray.showMessage(title, text, icon, 3500)

    def _activated(self, reason: QSystemTrayIcon.ActivationReason) -> None:
        if reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            self.settingsRequested.emit()

