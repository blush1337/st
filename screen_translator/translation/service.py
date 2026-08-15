from __future__ import annotations

from ..config import TranslationSettings
from .base import Translator
from .providers import (
    GoogleWebTranslator,
    LibreTranslateTranslator,
    PassthroughTranslator,
)


class TranslationService:
    def create_provider(self, settings: TranslationSettings) -> Translator:
        if settings.provider == "google_web":
            return GoogleWebTranslator(settings.timeout_seconds)
        if settings.provider == "libretranslate":
            return LibreTranslateTranslator(
                settings.libretranslate_url,
                settings.api_key,
                settings.timeout_seconds,
            )
        if settings.provider == "passthrough":
            return PassthroughTranslator()
        raise ValueError(f"Unsupported translation provider: {settings.provider}")

    def translate(self, text: str, settings: TranslationSettings) -> str:
        provider = self.create_provider(settings)
        source = None if settings.source_language == "auto" else settings.source_language
        return provider.translate(text, source, settings.target_language)

