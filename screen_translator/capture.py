from __future__ import annotations

import logging
from dataclasses import dataclass

import mss
from PIL import Image

from .diagnostics import log_event

log = logging.getLogger(__name__)


class CaptureError(RuntimeError):
    """A capture failure safe to summarize in the UI."""


@dataclass(frozen=True, slots=True)
class Selection:
    screen_index: int
    x: int
    y: int
    width: int
    height: int
    device_pixel_ratio: float
    global_x: int
    global_y: int
    global_width: int
    global_height: int


class ScreenCapture:
    def capture(self, selection: Selection) -> Image.Image:
        try:
            with mss.MSS() as source:
                monitor_index = selection.screen_index + 1
                if monitor_index >= len(source.monitors):
                    raise CaptureError("The selected monitor is no longer available.")
                monitor = source.monitors[monitor_index]
                scale = selection.device_pixel_ratio
                left = monitor["left"] + round(selection.x * scale)
                top = monitor["top"] + round(selection.y * scale)
                width = max(1, round(selection.width * scale))
                height = max(1, round(selection.height * scale))
                right_limit = monitor["left"] + monitor["width"]
                bottom_limit = monitor["top"] + monitor["height"]
                width = min(width, right_limit - left)
                height = min(height, bottom_limit - top)
                if width < 2 or height < 2:
                    raise CaptureError("The selected area is too small to capture.")
                log_event(
                    log,
                    "capture",
                    "physical_region_resolved",
                    level=logging.DEBUG,
                    monitor_index=monitor_index,
                    monitor_left=monitor["left"],
                    monitor_top=monitor["top"],
                    monitor_width=monitor["width"],
                    monitor_height=monitor["height"],
                    capture_left=left,
                    capture_top=top,
                    capture_width=width,
                    capture_height=height,
                )
                shot = source.grab(
                    {"left": left, "top": top, "width": width, "height": height}
                )
                return Image.frombytes("RGB", shot.size, shot.bgra, "raw", "BGRX")
        except CaptureError:
            raise
        except Exception as exc:
            log.exception("Screen capture failed")
            raise CaptureError("Windows could not capture the selected area.") from exc
