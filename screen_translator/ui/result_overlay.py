from __future__ import annotations

import math

from PySide6.QtCore import QRect, Qt, Signal
from PySide6.QtGui import QColor, QCloseEvent, QFont, QFontMetrics, QKeyEvent, QShowEvent
from PySide6.QtWidgets import (
    QApplication,
    QFrame,
    QHBoxLayout,
    QLabel,
    QProgressBar,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from ..config import OverlaySettings
from ..models import PipelineResult
from .geometry import position_near
from .motion import animate_window_in, animate_window_out
from .theme import material_theme


class TranslationOverlay(QFrame):
    closed = Signal()

    def __init__(
        self, result: PipelineResult, selection: QRect, settings: OverlaySettings
    ) -> None:
        super().__init__(None)
        self._allow_close = False
        self._closing = False
        self.setWindowFlags(
            Qt.WindowType.Tool
            | Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
        )
        self.setObjectName("translationPanel")
        theme = material_theme()
        background_alpha = round(settings.background_opacity * 2.55)
        text_alpha = round(settings.text_opacity * 2.55)
        surface = QColor(theme.surface)
        self.setStyleSheet(
            f"""
            QFrame#translationPanel {{
                background: rgba({surface.red()}, {surface.green()}, {surface.blue()}, {background_alpha});
                border: 1px solid {theme.outline};
                border-radius: 12px;
            }}
            QLabel, QTextEdit {{ color: rgba({QColor(theme.text).red()}, {QColor(theme.text).green()}, {QColor(theme.text).blue()}, {text_alpha}); }}
            QLabel#originalText {{ color: {theme.muted}; }}
            QTextEdit {{
                background: transparent;
                border: 0;
                selection-background-color: {theme.accent};
                selection-color: {theme.on_accent};
            }}
            QPushButton {{
                min-height: 32px;
                color: {theme.text};
                background: {theme.surface_variant};
                border: 1px solid {theme.outline};
                border-radius: 8px;
                padding: 2px 14px;
            }}
            QPushButton:hover {{ background: {theme.hover}; }}
            QPushButton:pressed {{ background: {theme.outline}; }}
            QPushButton#primaryButton {{
                color: {theme.on_accent};
                background: {theme.accent};
                border-color: {theme.accent};
            }}
            """
        )
        layout = QVBoxLayout(self)
        panel_padding = max(10, settings.padding)
        layout.setContentsMargins(panel_padding, panel_padding, panel_padding, panel_padding)
        layout.setSpacing(10)

        if settings.show_original:
            original_label = QLabel(result.original_text)
            original_label.setObjectName("originalText")
            original_label.setWordWrap(True)
            layout.addWidget(original_label)

        self.text = QTextEdit(result.translated_text)
        self.text.setReadOnly(True)
        self.text.setAcceptRichText(False)
        font_size = settings.font_size
        if settings.automatic_font_size and len(result.translated_text) > 700:
            font_size = max(9, font_size - 2)
        self.text.setFont(QFont(settings.font_family, font_size))
        self.text.document().setDocumentMargin(0)
        metrics = QFontMetrics(self.text.font())
        longest_line = max(result.translated_text.splitlines(), key=len, default="")
        text_width = min(500, max(260, metrics.horizontalAdvance(longest_line) + 14))
        self.text.document().setTextWidth(text_width - 12)
        text_height = min(
            300, max(48, math.ceil(self.text.document().size().height()) + 8)
        )
        self.text.setFixedSize(text_width, text_height)
        layout.addWidget(self.text)

        buttons = QHBoxLayout()
        buttons.addStretch()
        copy_button = QPushButton("Copy")
        copy_button.setObjectName("primaryButton")
        copy_button.clicked.connect(self.copy_text)
        close_button = QPushButton("Close")
        close_button.clicked.connect(self.request_close)
        buttons.addWidget(copy_button)
        buttons.addWidget(close_button)
        layout.addLayout(buttons)

        self.adjustSize()
        screen = QApplication.screenAt(selection.center()) or QApplication.primaryScreen()
        self.move(
            position_near(
                selection,
                self.sizeHint(),
                screen.availableGeometry(),
                preference=settings.position,
            )
        )

    def copy_text(self) -> None:
        QApplication.clipboard().setText(self.text.toPlainText())

    def closeEvent(self, event: QCloseEvent) -> None:
        if not self._allow_close:
            event.ignore()
            self.request_close()
            return
        self.closed.emit()
        super().closeEvent(event)

    def request_close(self) -> None:
        if self._closing:
            return
        self._closing = True
        animate_window_out(self, self._finish_close, offset_y=5)

    def _finish_close(self) -> None:
        self._allow_close = True
        self.close()

    def showEvent(self, event: QShowEvent) -> None:
        super().showEvent(event)
        animate_window_in(self, offset_y=7)

    def keyPressEvent(self, event: QKeyEvent) -> None:
        if event.key() == Qt.Key.Key_Escape:
            self.request_close()
        else:
            super().keyPressEvent(event)


class ProcessingPopup(QFrame):
    def __init__(self, selection: QRect) -> None:
        super().__init__(None)
        self.setWindowFlags(
            Qt.WindowType.Tool
            | Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.WindowDoesNotAcceptFocus
        )
        self.setObjectName("processingPanel")
        theme = material_theme()
        self.setStyleSheet(
            f"""
            QFrame#processingPanel {{
                background: {theme.surface};
                border: 1px solid {theme.outline};
                border-radius: 10px;
            }}
            QLabel {{ color: {theme.text}; }}
            QProgressBar {{
                background: {theme.surface_variant};
                border: 0;
                border-radius: 2px;
                min-height: 4px;
                max-height: 4px;
                text-align: center;
            }}
            QProgressBar::chunk {{
                background: {theme.accent};
                border-radius: 2px;
            }}
            """
        )
        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 11, 14, 11)
        layout.setSpacing(9)
        layout.addWidget(QLabel("Reading and translating…"))
        progress = QProgressBar()
        progress.setRange(0, 0)
        progress.setTextVisible(False)
        progress.setFixedWidth(190)
        layout.addWidget(progress)
        self.adjustSize()
        screen = QApplication.screenAt(selection.center()) or QApplication.primaryScreen()
        self.move(position_near(selection, self.sizeHint(), screen.availableGeometry()))

    def showEvent(self, event: QShowEvent) -> None:
        super().showEvent(event)
        animate_window_in(self, offset_y=5)
