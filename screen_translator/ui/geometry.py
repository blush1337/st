from __future__ import annotations

from PySide6.QtCore import QPoint, QRect, QSize


def position_near(
    selection: QRect,
    panel: QSize,
    available: QRect,
    gap: int = 8,
    preference: str = "automatic",
) -> QPoint:
    x = selection.left()
    below = selection.bottom() + gap + 1
    above = selection.top() - panel.height() - gap
    below_fits = below + panel.height() <= available.bottom() + 1
    above_fits = above >= available.top()
    if preference == "above" and above_fits:
        y = above
    elif preference == "below" and below_fits:
        y = below
    elif below_fits:
        y = below
    elif above_fits:
        y = above
    else:
        y = min(max(selection.top(), available.top()), available.bottom() - panel.height() + 1)
    x = min(max(x, available.left()), available.right() - panel.width() + 1)
    y = min(max(y, available.top()), available.bottom() - panel.height() + 1)
    return QPoint(x, y)
