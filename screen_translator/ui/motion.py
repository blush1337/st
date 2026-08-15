from __future__ import annotations

from PySide6.QtCore import (
    QEasingCurve,
    QParallelAnimationGroup,
    QPoint,
    QPropertyAnimation,
)
from PySide6.QtWidgets import QGraphicsOpacityEffect, QWidget


MOTION_DURATION_MS = 170


def animate_window_in(widget: QWidget, offset_y: int = 7) -> None:
    end_position = widget.pos()
    widget.move(end_position + QPoint(0, offset_y))
    widget.setWindowOpacity(0.0)
    opacity = QPropertyAnimation(widget, b"windowOpacity")
    opacity.setDuration(MOTION_DURATION_MS)
    opacity.setStartValue(0.0)
    opacity.setEndValue(1.0)
    opacity.setEasingCurve(QEasingCurve.Type.OutCubic)
    position = QPropertyAnimation(widget, b"pos")
    position.setDuration(MOTION_DURATION_MS)
    position.setStartValue(widget.pos())
    position.setEndValue(end_position)
    position.setEasingCurve(QEasingCurve.Type.OutCubic)
    group = QParallelAnimationGroup(widget)
    group.addAnimation(opacity)
    group.addAnimation(position)
    widget._material_window_animation = group  # type: ignore[attr-defined]

    def cleanup() -> None:
        widget._material_window_animation = None  # type: ignore[attr-defined]
        group.deleteLater()

    group.finished.connect(cleanup)
    group.start()


def animate_opacity_in(widget: QWidget, duration_ms: int = 150) -> None:
    widget.setWindowOpacity(0.0)
    animation = QPropertyAnimation(widget, b"windowOpacity")
    animation.setDuration(duration_ms)
    animation.setStartValue(0.0)
    animation.setEndValue(1.0)
    animation.setEasingCurve(QEasingCurve.Type.OutCubic)
    widget._material_window_animation = animation  # type: ignore[attr-defined]

    def cleanup() -> None:
        widget._material_window_animation = None  # type: ignore[attr-defined]
        animation.deleteLater()

    animation.finished.connect(cleanup)
    animation.start()


def animate_window_out(widget: QWidget, finished: object, offset_y: int = 5) -> None:
    start_position = widget.pos()
    opacity = QPropertyAnimation(widget, b"windowOpacity")
    opacity.setDuration(140)
    opacity.setStartValue(widget.windowOpacity())
    opacity.setEndValue(0.0)
    opacity.setEasingCurve(QEasingCurve.Type.InCubic)
    position = QPropertyAnimation(widget, b"pos")
    position.setDuration(140)
    position.setStartValue(start_position)
    position.setEndValue(start_position + QPoint(0, offset_y))
    position.setEasingCurve(QEasingCurve.Type.InCubic)
    group = QParallelAnimationGroup(widget)
    group.addAnimation(opacity)
    group.addAnimation(position)
    widget._material_window_animation = group  # type: ignore[attr-defined]

    def cleanup() -> None:
        widget._material_window_animation = None  # type: ignore[attr-defined]
        group.deleteLater()

    group.finished.connect(cleanup)
    group.finished.connect(finished)  # type: ignore[arg-type]
    group.start()


def animate_page_in(widget: QWidget) -> None:
    effect = QGraphicsOpacityEffect(widget)
    widget.setGraphicsEffect(effect)
    animation = QPropertyAnimation(effect, b"opacity", widget)
    animation.setDuration(150)
    animation.setStartValue(0.35)
    animation.setEndValue(1.0)
    animation.setEasingCurve(QEasingCurve.Type.OutCubic)

    def cleanup() -> None:
        widget.setGraphicsEffect(None)
        widget._material_page_animation = None  # type: ignore[attr-defined]
        animation.deleteLater()

    animation.finished.connect(cleanup)
    widget._material_page_animation = animation  # type: ignore[attr-defined]
    animation.start()
