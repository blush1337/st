from __future__ import annotations

from PySide6.QtCore import QPoint, QRect, Qt, Signal
from PySide6.QtGui import QColor, QGuiApplication, QKeyEvent, QMouseEvent, QPainter, QPen
from PySide6.QtWidgets import QApplication, QWidget

from ..capture import Selection


class SelectionWindow(QWidget):
    confirmed = Signal(object)
    cancelled = Signal()

    def __init__(self, screen_index: int) -> None:
        super().__init__(None)
        self.screen_index = screen_index
        self.screen = QGuiApplication.screens()[screen_index]
        self.origin: QPoint | None = None
        self.current: QPoint | None = None
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setCursor(Qt.CursorShape.CrossCursor)
        self.setMouseTracking(True)

    def show_on_screen(self) -> None:
        self.setGeometry(self.screen.geometry())
        self.show()
        self.raise_()

    def selection_rect(self) -> QRect:
        if self.origin is None or self.current is None:
            return QRect()
        return QRect(self.origin, self.current).normalized()

    def paintEvent(self, _event: object) -> None:
        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor(0, 0, 0, 92))
        selected = self.selection_rect()
        if selected.isValid() and not selected.isEmpty():
            painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_Clear)
            painter.fillRect(selected, Qt.GlobalColor.transparent)
            painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceOver)
            painter.setPen(QPen(QColor(0, 120, 212), 2))
            painter.drawRect(selected.adjusted(0, 0, -1, -1))
            label = f"{selected.width()} × {selected.height()}"
            label_rect = QRect(selected.left(), max(4, selected.top() - 27), 130, 23)
            painter.fillRect(label_rect, QColor(32, 32, 32, 230))
            painter.setPen(Qt.GlobalColor.white)
            painter.drawText(label_rect.adjusted(7, 0, -4, 0), Qt.AlignmentFlag.AlignVCenter, label)
        elif self.screen_index == 0:
            painter.setPen(Qt.GlobalColor.white)
            painter.drawText(
                self.rect().adjusted(0, 28, 0, 0),
                Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignTop,
                "Drag to select text  •  Esc to cancel",
            )

    def mousePressEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self.origin = event.position().toPoint()
            self.current = self.origin
            self.grabMouse()
            self.update()

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        if self.origin is not None:
            self.current = event.position().toPoint()
            self.update()

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        if event.button() != Qt.MouseButton.LeftButton or self.origin is None:
            return
        self.current = event.position().toPoint()
        self.releaseMouse()
        rect = self.selection_rect().intersected(self.rect())
        self.origin = None
        self.current = None
        if rect.width() < 8 or rect.height() < 8:
            self.update()
            return
        global_top_left = self.mapToGlobal(rect.topLeft())
        selection = Selection(
            screen_index=self.screen_index,
            x=rect.x(),
            y=rect.y(),
            width=rect.width(),
            height=rect.height(),
            device_pixel_ratio=self.screen.devicePixelRatio(),
            global_x=global_top_left.x(),
            global_y=global_top_left.y(),
            global_width=rect.width(),
            global_height=rect.height(),
        )
        self.confirmed.emit(selection)

    def keyPressEvent(self, event: QKeyEvent) -> None:
        if event.key() == Qt.Key.Key_Escape:
            self.cancelled.emit()
        else:
            super().keyPressEvent(event)


class SelectionController:
    def __init__(self, on_selected: object, on_cancelled: object) -> None:
        self.windows: list[SelectionWindow] = []
        self.on_selected = on_selected
        self.on_cancelled = on_cancelled

    def start(self) -> None:
        self.close()
        for index, _screen in enumerate(QGuiApplication.screens()):
            window = SelectionWindow(index)
            window.confirmed.connect(self._confirmed)
            window.cancelled.connect(self._cancelled)
            self.windows.append(window)
            window.show_on_screen()
        if self.windows:
            self.windows[0].activateWindow()
            self.windows[0].grabKeyboard()

    def close(self) -> None:
        for window in self.windows:
            if window.keyboardGrabber() is window:
                window.releaseKeyboard()
            window.close()
            window.deleteLater()
        self.windows.clear()

    def _confirmed(self, selection: Selection) -> None:
        self.close()
        self.on_selected(selection)

    def _cancelled(self) -> None:
        self.close()
        self.on_cancelled()

