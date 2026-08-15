from __future__ import annotations

import os
from pathlib import Path


APP_DIR_NAME = "Screen Region Translator"


def app_data_dir() -> Path:
    base = os.environ.get("LOCALAPPDATA")
    if base:
        return Path(base) / APP_DIR_NAME
    return Path.home() / ".screen-region-translator"


def settings_path() -> Path:
    return app_data_dir() / "settings.json"


def log_path() -> Path:
    return app_data_dir() / "screen-translator.log"

