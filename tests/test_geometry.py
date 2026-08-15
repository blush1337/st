from __future__ import annotations

from PySide6.QtCore import QRect, QSize

from screen_translator.ui.geometry import position_near


def test_panel_prefers_below_selection(qapp) -> None:
    available = QRect(0, 0, 1920, 1040)
    selection = QRect(100, 100, 300, 80)

    point = position_near(selection, QSize(400, 200), available)

    assert point.x() == 100
    assert point.y() == 188


def test_panel_moves_above_near_bottom(qapp) -> None:
    available = QRect(-1280, 0, 1280, 984)
    selection = QRect(-600, 900, 300, 70)

    point = position_near(selection, QSize(420, 240), available)

    assert point.x() == -600
    assert point.y() == 652
    assert available.contains(QRect(point, QSize(420, 240)))


def test_position_preference_is_honored_when_it_fits(qapp) -> None:
    available = QRect(0, 0, 1000, 800)
    selection = QRect(200, 350, 200, 50)

    above = position_near(
        selection, QSize(300, 100), available, preference="above"
    )

    assert above.y() == 242

