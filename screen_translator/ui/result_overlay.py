from __future__ import annotations

import math

from PySide6.QtCore import QRect, Qt, QTimer
from PySide6.QtGui import QFont, QFontMetrics, QKeyEvent
from PySide6.QtWidgets import (
    QApplication,
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from ..config import OverlaySettings
from ..models import PipelineResult
from .geometry import position_near


class TranslationOverlay(QFrame):
    def __init__(
        self, result: PipelineResult, selection: QRect, settings: OverlaySettings
    ) -> None:
        super().__init__(None)
        self.setWindowFlags(
            Qt.WindowType.Popup
            | Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
        )
        self.setObjectName("translationPanel")
        background_alpha = round(settings.background_opacity * 2.55)
        text_alpha = round(settings.text_opacity * 2.55)
        self.setStyleSheet(
            f"""
            QFrame#translationPanel {{
                background: rgba(32, 32, 32, {background_alpha});
                border: 1px solid rgba(255, 255, 255, 45);
                border-radius: 4px;
            }}
            QLabel, QTextEdit {{ color: rgba(255, 255, 255, {text_alpha}); }}
            QTextEdit {{ background: transparent; border: 0; selection-background-color: #0078d4; }}
            QPushButton {{
                color: white; background: #3a3a3a; border: 1px solid #5a5a5a;
                border-radius: 3px; padding: 5px 12px;
            }}
            QPushButton:hover {{ background: #464646; }}
            """
        )
        layout = QVBoxLayout(self)
        layout.setContentsMargins(settings.padding, settings.padding, settings.padding, settings.padding)
        layout.setSpacing(7)

        if settings.show_original:
            original_label = QLabel(result.original_text)
            original_label.setWordWrap(True)
            original_label.setStyleSheet("color: #b8b8b8;")
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
        copy_button.clicked.connect(self.copy_text)
        close_button = QPushButton("Close")
        close_button.clicked.connect(self.close)
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
        if settings.auto_dismiss:
            QTimer.singleShot(settings.dismiss_seconds * 1000, self.close)

    def copy_text(self) -> None:
        QApplication.clipboard().setText(self.text.toPlainText())

    def keyPressEvent(self, event: QKeyEvent) -> None:
        if event.key() == Qt.Key.Key_Escape:
            self.close()
        else:
            super().keyPressEvent(event)


class ProcessingPopup(QLabel):
    def __init__(self, selection: QRect) -> None:
        super().__init__("Reading and translating…", None)
        self.setWindowFlags(
            Qt.WindowType.Tool
            | Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.WindowDoesNotAcceptFocus
        )
        self.setStyleSheet(
            "QLabel { background: #202020; color: white; border: 1px solid #555; "
            "border-radius: 3px; padding: 8px 12px; }"
        )
        self.adjustSize()
        screen = QApplication.screenAt(selection.center()) or QApplication.primaryScreen()
        self.move(position_near(selection, self.sizeHint(), screen.availableGeometry()))
