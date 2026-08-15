from __future__ import annotations

from typing import Any

import requests

from .base import TranslationError, Translator


class GoogleWebTranslator(Translator):
    """No-key Google web endpoint. Useful for personal use, but not an SLA API."""

    endpoint = "https://translate.googleapis.com/translate_a/single"

    def __init__(self, timeout: int = 15) -> None:
        self.timeout = timeout

    def translate(
        self, text: str, source_language: str | None, target_language: str
    ) -> str:
        try:
            response = requests.get(
                self.endpoint,
                params={
                    "client": "gtx",
                    "sl": source_language or "auto",
                    "tl": target_language,
                    "dt": "t",
                    "q": text,
                },
                timeout=self.timeout,
            )
            response.raise_for_status()
            payload: Any = response.json()
            translated = "".join(
                segment[0]
                for segment in payload[0]
                if isinstance(segment, list) and segment and segment[0]
            )
            if not translated.strip():
                raise TranslationError("The translation service returned no text.")
            return translated
        except TranslationError:
            raise
        except (requests.RequestException, ValueError, KeyError, TypeError, IndexError) as exc:
            raise TranslationError(
                "Google Web could not translate the selected text."
            ) from exc


class LibreTranslateTranslator(Translator):
    def __init__(self, base_url: str, api_key: str, timeout: int = 15) -> None:
        self.endpoint = f"{base_url.rstrip('/')}/translate"
        self.api_key = api_key
        self.timeout = timeout

    def translate(
        self, text: str, source_language: str | None, target_language: str
    ) -> str:
        body = {
            "q": text,
            "source": source_language or "auto",
            "target": target_language,
            "format": "text",
        }
        if self.api_key:
            body["api_key"] = self.api_key
        try:
            response = requests.post(self.endpoint, json=body, timeout=self.timeout)
            if response.status_code in {401, 403}:
                raise TranslationError("LibreTranslate rejected the API key.")
            if response.status_code == 429:
                raise TranslationError("LibreTranslate rate limit reached.")
            response.raise_for_status()
            translated = response.json().get("translatedText", "")
            if not isinstance(translated, str) or not translated.strip():
                raise TranslationError("LibreTranslate returned no text.")
            return translated
        except TranslationError:
            raise
        except (requests.RequestException, ValueError, AttributeError) as exc:
            raise TranslationError("LibreTranslate is unavailable.") from exc


class PassthroughTranslator(Translator):
    def translate(
        self, text: str, source_language: str | None, target_language: str
    ) -> str:
        return text

