from __future__ import annotations

import json
import logging
import time
from contextlib import contextmanager
from collections.abc import Iterator


def _fields(values: dict[str, object]) -> str:
    if not values:
        return ""
    rendered = " ".join(
        f"{key}={json.dumps(value, ensure_ascii=False, default=str)}"
        for key, value in values.items()
    )
    return f" {rendered}"


def log_event(
    logger: logging.Logger,
    stage: str,
    event: str,
    *,
    level: int = logging.INFO,
    **values: object,
) -> None:
    logger.log(level, "stage=%s event=%s%s", stage, event, _fields(values))


@contextmanager
def logged_stage(
    logger: logging.Logger,
    stage: str,
    *,
    operation_id: str,
    **values: object,
) -> Iterator[None]:
    started = time.perf_counter()
    log_event(logger, stage, "started", operation_id=operation_id, **values)
    try:
        yield
    except Exception as exc:
        duration_ms = round((time.perf_counter() - started) * 1000, 1)
        log_event(
            logger,
            stage,
            "failed",
            level=logging.ERROR,
            operation_id=operation_id,
            duration_ms=duration_ms,
            error_type=type(exc).__name__,
        )
        if logger.isEnabledFor(logging.DEBUG):
            logger.debug(
                "Diagnostic traceback for stage=%s operation_id=%s",
                stage,
                operation_id,
                exc_info=True,
            )
        raise
    else:
        duration_ms = round((time.perf_counter() - started) * 1000, 1)
        log_event(
            logger,
            stage,
            "completed",
            operation_id=operation_id,
            duration_ms=duration_ms,
        )
