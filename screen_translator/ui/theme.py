from __future__ import annotations

from dataclasses import dataclass

from PySide6.QtGui import QColor, QPalette
from PySide6.QtWidgets import QApplication


@dataclass(frozen=True, slots=True)
class MaterialTheme:
    background: str
    surface: str
    surface_variant: str
    hover: str
    outline: str
    text: str
    muted: str
    accent: str
    on_accent: str


def _hex(color: QColor) -> str:
    return color.name(QColor.NameFormat.HexRgb)


def material_theme() -> MaterialTheme:
    palette = QApplication.palette()
    dark = palette.color(QPalette.ColorRole.Window).lightness() < 128
    accent = palette.color(QPalette.ColorRole.Highlight)
    on_accent = palette.color(QPalette.ColorRole.HighlightedText)
    if dark:
        return MaterialTheme(
            background="#17181b",
            surface="#202226",
            surface_variant="#2a2d32",
            hover="#34373d",
            outline="#44484f",
            text="#f1f2f4",
            muted="#b6bac2",
            accent=_hex(accent),
            on_accent=_hex(on_accent),
        )
    return MaterialTheme(
        background="#f7f8fa",
        surface="#ffffff",
        surface_variant="#eef0f3",
        hover="#e3e6eb",
        outline="#d5d9df",
        text="#1d1f23",
        muted="#626872",
        accent=_hex(accent),
        on_accent=_hex(on_accent),
    )


def settings_stylesheet(theme: MaterialTheme) -> str:
    return f"""
        QDialog#settingsWindow {{
            background: {theme.background};
            color: {theme.text};
        }}
        QWidget#settingsPage, QScrollArea, QScrollArea > QWidget > QWidget {{
            background: transparent;
        }}
        QLabel, QCheckBox, QGroupBox {{ color: {theme.text}; }}
        QLabel#windowTitle {{ font-size: 21px; font-weight: 600; }}
        QLabel#pageTitle {{ font-size: 18px; font-weight: 600; }}
        QLabel#description {{ color: {theme.muted}; font-size: 8.5pt; }}

        QListWidget#navigation {{
            background: {theme.surface};
            color: {theme.text};
            border: 1px solid {theme.outline};
            border-radius: 12px;
            padding: 8px;
            outline: 0;
        }}
        QListWidget#navigation::item {{
            min-height: 30px;
            padding: 7px 11px;
            margin: 2px 0;
            border-radius: 8px;
        }}
        QListWidget#navigation::item:hover {{ background: {theme.surface_variant}; }}
        QListWidget#navigation::item:selected {{
            background: {theme.accent};
            color: {theme.on_accent};
        }}

        QGroupBox {{
            background: {theme.surface};
            border: 1px solid {theme.outline};
            border-radius: 12px;
            font-weight: 600;
            margin-top: 17px;
            padding: 17px 14px 14px 14px;
        }}
        QGroupBox::title {{
            subcontrol-origin: margin;
            subcontrol-position: top left;
            left: 13px;
            padding: 0 6px;
            color: {theme.text};
            background: {theme.background};
        }}

        QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox, QFontComboBox {{
            min-height: 32px;
            background: {theme.surface_variant};
            color: {theme.text};
            border: 1px solid {theme.outline};
            border-radius: 8px;
            padding: 1px 9px;
            selection-background-color: {theme.accent};
            selection-color: {theme.on_accent};
        }}
        QLineEdit:hover, QComboBox:hover, QSpinBox:hover,
        QDoubleSpinBox:hover, QFontComboBox:hover {{ border-color: {theme.muted}; }}
        QLineEdit:focus, QComboBox:focus, QSpinBox:focus,
        QDoubleSpinBox:focus, QFontComboBox:focus {{ border: 2px solid {theme.accent}; }}
        QLineEdit:disabled, QComboBox:disabled, QSpinBox:disabled,
        QDoubleSpinBox:disabled, QFontComboBox:disabled {{
            color: {theme.muted};
            background: {theme.background};
        }}
        QComboBox::drop-down {{ width: 28px; border: 0; }}

        QPushButton {{
            min-height: 34px;
            padding: 1px 15px;
            background: {theme.surface_variant};
            color: {theme.text};
            border: 1px solid {theme.outline};
            border-radius: 8px;
            font-weight: 500;
        }}
        QPushButton:hover {{ background: {theme.hover}; }}
        QPushButton:pressed {{ background: {theme.outline}; }}
        QPushButton#primaryButton {{
            background: {theme.accent};
            color: {theme.on_accent};
            border: 1px solid {theme.accent};
        }}
        QPushButton#primaryButton:hover {{ background: {theme.accent}; }}

        QScrollBar:vertical {{
            background: transparent;
            width: 10px;
            margin: 3px;
        }}
        QScrollBar::handle:vertical {{
            background: {theme.outline};
            min-height: 28px;
            border-radius: 3px;
        }}
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}
        QToolTip {{
            background: {theme.surface_variant};
            color: {theme.text};
            border: 1px solid {theme.outline};
            border-radius: 6px;
            padding: 6px 8px;
        }}
    """


def menu_stylesheet(theme: MaterialTheme) -> str:
    return f"""
        QMenu {{
            background: {theme.surface};
            color: {theme.text};
            border: 1px solid {theme.outline};
            border-radius: 10px;
            padding: 7px;
        }}
        QMenu::item {{
            padding: 8px 30px 8px 12px;
            margin: 1px 0;
            border-radius: 6px;
        }}
        QMenu::item:selected {{
            background: {theme.accent};
            color: {theme.on_accent};
        }}
        QMenu::item:disabled {{ color: {theme.muted}; }}
        QMenu::separator {{
            height: 1px;
            background: {theme.outline};
            margin: 6px 8px;
        }}
    """

