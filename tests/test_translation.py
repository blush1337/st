from __future__ import annotations

from unittest.mock import Mock, patch

import pytest

from screen_translator.translation.base import TranslationError
from screen_translator.translation.providers import (
    GoogleWebTranslator,
    LibreTranslateTranslator,
)


def test_google_web_joins_response_segments() -> None:
    response = Mock()
    response.json.return_value = [[['Привет ', 'Hello '], ['мир', 'world']]]
    response.raise_for_status.return_value = None
    with patch("screen_translator.translation.providers.requests.get", return_value=response):
        translated = GoogleWebTranslator().translate("Hello world", None, "ru")
    assert translated == "Привет мир"


def test_libretranslate_sends_credentials_without_exposing_them() -> None:
    response = Mock(status_code=200)
    response.json.return_value = {"translatedText": "Hallo"}
    response.raise_for_status.return_value = None
    with patch("screen_translator.translation.providers.requests.post", return_value=response) as post:
        translated = LibreTranslateTranslator("https://example.test/", "secret").translate(
            "Hello", "en", "de"
        )
    assert translated == "Hallo"
    assert post.call_args.kwargs["json"]["api_key"] == "secret"


def test_libretranslate_reports_rate_limit() -> None:
    response = Mock(status_code=429)
    with patch("screen_translator.translation.providers.requests.post", return_value=response):
        with pytest.raises(TranslationError, match="rate limit"):
            LibreTranslateTranslator("https://example.test", "").translate(
                "Hello", "en", "de"
            )

