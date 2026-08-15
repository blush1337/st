from __future__ import annotations

import json
import logging
import os
from dataclasses import asdict, dataclass, field, fields, is_dataclass
from pathlib import Path
from typing import Any, TypeVar

from .paths import settings_path

log = logging.getLogger(__name__)
T = TypeVar("T")


@dataclass(slots=True)
class GeneralSettings:
    launch_at_startup: bool = False
    start_minimized: bool = False
    minimize_to_tray: bool = True
    tray_notifications: bool = True
    close_behavior: str = "tray"


@dataclass(slots=True)
class HotkeySettings:
    shortcut: str = "ctrl+shift+t"
    enabled: bool = True


@dataclass(slots=True)
class TranslationSettings:
    source_language: str = "auto"
    target_language: str = "ru"
    provider: str = "google_web"
    libretranslate_url: str = "https://libretranslate.com"
    api_key: str = ""
    timeout_seconds: int = 15


@dataclass(slots=True)
class OCRSettings:
    engine: str = "rapidocr"
    language: str = "en_zh"
    confidence_threshold: float = 0.55
    preprocess: bool = True
    gpu: bool = False


@dataclass(slots=True)
class OverlaySettings:
    font_family: str = "Segoe UI"
    font_size: int = 11
    automatic_font_size: bool = True
    text_opacity: int = 100
    background_opacity: int = 96
    padding: int = 12
    position: str = "automatic"
    show_original: bool = False
    auto_dismiss: bool = False
    dismiss_seconds: int = 8


@dataclass(slots=True)
class AppSettings:
    general: GeneralSettings = field(default_factory=GeneralSettings)
    hotkey: HotkeySettings = field(default_factory=HotkeySettings)
    translation: TranslationSettings = field(default_factory=TranslationSettings)
    ocr: OCRSettings = field(default_factory=OCRSettings)
    overlay: OverlaySettings = field(default_factory=OverlaySettings)


def _merge_dataclass(cls: type[T], value: Any) -> T:
    if not isinstance(value, dict):
        return cls()
    allowed = {item.name for item in fields(cls)}
    return cls(**{key: val for key, val in value.items() if key in allowed})


class SettingsStore:
    def __init__(self, path: Path | None = None) -> None:
        self.path = path or settings_path()

    def load(self) -> AppSettings:
        try:
            raw = json.loads(self.path.read_text(encoding="utf-8"))
            if not isinstance(raw, dict):
                raise ValueError("settings root is not an object")
            return AppSettings(
                general=_merge_dataclass(GeneralSettings, raw.get("general")),
                hotkey=_merge_dataclass(HotkeySettings, raw.get("hotkey")),
                translation=_merge_dataclass(
                    TranslationSettings, raw.get("translation")
                ),
                ocr=_merge_dataclass(OCRSettings, raw.get("ocr")),
                overlay=_merge_dataclass(OverlaySettings, raw.get("overlay")),
            )
        except FileNotFoundError:
            return AppSettings()
        except (OSError, ValueError, TypeError, json.JSONDecodeError):
            log.exception("Could not read settings; defaults will be used")
            return AppSettings()

    def save(self, settings: AppSettings) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temporary = self.path.with_suffix(".tmp")
        data = asdict(settings)
        temporary.write_text(
            json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8"
        )
        os.replace(temporary, self.path)

