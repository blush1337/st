from __future__ import annotations

import logging
from logging.handlers import RotatingFileHandler

from .paths import log_path


def configure_logging() -> None:
    path = log_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    handler = RotatingFileHandler(
        path, maxBytes=1_000_000, backupCount=3, encoding="utf-8"
    )
    handler.set_name("screen-region-translator-file")
    handler.setFormatter(
        logging.Formatter(
            "%(asctime)s %(levelname)s %(name)s %(message)s",
            datefmt="%Y-%m-%dT%H:%M:%S",
        )
    )
    root = logging.getLogger()
    if any(item.get_name() == handler.get_name() for item in root.handlers):
        handler.close()
        return
    root.setLevel(logging.INFO)
    root.addHandler(handler)
