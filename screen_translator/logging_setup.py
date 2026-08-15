from __future__ import annotations

import logging
import sys
from logging.handlers import RotatingFileHandler

from .paths import log_path


FORMAT = "%(asctime)s.%(msecs)03d %(levelname)s %(name)s %(message)s"
DATE_FORMAT = "%Y-%m-%dT%H:%M:%S"


def configure_logging(debug: bool = False) -> None:
    path = log_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    application_logger = logging.getLogger("screen_translator")
    application_logger.setLevel(logging.DEBUG if debug else logging.INFO)
    root = logging.getLogger()
    root.setLevel(logging.INFO)

    handler = RotatingFileHandler(
        path, maxBytes=1_000_000, backupCount=3, encoding="utf-8"
    )
    handler.set_name("screen-region-translator-file")
    handler.setLevel(logging.DEBUG if debug else logging.INFO)
    handler.setFormatter(logging.Formatter(FORMAT, datefmt=DATE_FORMAT))
    if any(item.get_name() == handler.get_name() for item in root.handlers):
        handler.close()
        return
    root.addHandler(handler)

    if debug:
        console = logging.StreamHandler(sys.stderr)
        console.set_name("screen-region-translator-console")
        console.setLevel(logging.DEBUG)
        console.setFormatter(logging.Formatter(FORMAT, datefmt=DATE_FORMAT))
        root.addHandler(console)
