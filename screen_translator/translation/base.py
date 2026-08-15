from __future__ import annotations

from abc import ABC, abstractmethod


class TranslationError(RuntimeError):
    """A translation failure safe to summarize in the UI."""


class Translator(ABC):
    @abstractmethod
    def translate(
        self,
        text: str,
        source_language: str | None,
        target_language: str,
    ) -> str:
        raise NotImplementedError

