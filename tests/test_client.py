"""Unit tests for the synchronous Nativ client."""

import os
import pytest
import httpx

from nativ import (
    Nativ,
    AuthenticationError,
    InsufficientCreditsError,
    ValidationError,
    NotFoundError,
    RateLimitError,
    ServerError,
)
from nativ._client import _resolve_api_key, _build_translate_body, DEFAULT_BASE_URL

API_KEY = "nativ_test_00000000000000000000000000000000"
BASE = "https://api.test.usenativ.com"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


TRANSLATE_RESPONSE = {
    "translated_text": "Bonjour le monde",
    "metadata": {"word_count": 2, "cost": 100},
    "tm_match": {
        "score": 85.5,
        "match_type": "fuzzy",
        "source_text": "Hello world",
        "target_text": "Bonjour le monde",
        "tm_source": "manual",
        "tm_source_name": "My TM",
        "tm_id": "abc-123",
        "top_matches": [
            {
                "tm_id": "abc-123",
                "score": 85.5,
                "match_type": "fuzzy",
                "source_text": "Hello world",
                "target_text": "Bonjour le monde",
                "information_source": "manual",
                "source_name": "My TM",
            }
        ],
    },
    "rationale": "Chose formal register.",
    "backtranslation": "Hello world",
}


# ---------------------------------------------------------------------------
# Auth / config
# ---------------------------------------------------------------------------


class TestResolveApiKey:
    def test_explicit_key(self):
        assert _resolve_api_key("nativ_foo") == "nativ_foo"

    def test_env_var(self, monkeypatch):
        monkeypatch.setenv("NATIV_API_KEY", "nativ_from_env")
        assert _resolve_api_key(None) == "nativ_from_env"

    def test_missing_raises(self, monkeypatch):
        monkeypatch.delenv("NATIV_API_KEY", raising=False)
        with pytest.raises(AuthenticationError):
            _resolve_api_key(None)


class TestClientInit:
    def test_default_base_url(self, monkeypatch):
        monkeypatch.delenv("NATIV_API_URL", raising=False)
        c = Nativ(api_key=API_KEY)
        assert c._base_url == DEFAULT_BASE_URL

    def test_custom_base_url(self):
        c = Nativ(api_key=API_KEY, base_url="https://custom.api.com/")
        assert c._base_url == "https://custom.api.com"

    def test_env_base_url(self, monkeypatch):
        monkeypatch.setenv("NATIV_API_URL", "https://env.api.com")
        c = Nativ(api_key=API_KEY)
        assert c._base_url == "https://env.api.com"

    def test_context_manager(self):
        with Nativ(api_key=API_KEY) as c:
            assert c._api_key == API_KEY


# ---------------------------------------------------------------------------
# Translation
# ---------------------------------------------------------------------------


class TestTranslate:
    def test_translate_basic(self, httpx_mock):
        httpx_mock.add_response(
            url=f"{BASE}/text/culturalize",
            method="POST",
            json=TRANSLATE_RESPONSE,
        )
        c = Nativ(api_key=API_KEY, base_url=BASE)
        result = c.translate("Hello world", "French")

        assert result.translated_text == "Bonjour le monde"
        assert result.metadata.word_count == 2
        assert result.metadata.cost == 100
        assert result.tm_match is not None
        assert result.tm_match.score == 85.5
        assert len(result.tm_match.top_matches) == 1
        assert result.rationale == "Chose formal register."
        assert result.backtranslation == "Hello world"

    def test_translate_no_tm(self, httpx_mock):
        httpx_mock.add_response(
            url=f"{BASE}/text/culturalize",
            method="POST",
            json={
                "translated_text": "Hola",
                "metadata": {"word_count": 1, "cost": 100},
            },
        )
        c = Nativ(api_key=API_KEY, base_url=BASE)
        result = c.translate("Hi", "Spanish")
        assert result.translated_text == "Hola"
        assert result.tm_match is None

    def test_translate_batch(self, httpx_mock):
        for text in ["Sign up", "Log in"]:
            httpx_mock.add_response(
                url=f"{BASE}/text/culturalize",
                method="POST",
                json={
                    "translated_text": f"_{text}_de",
                    "metadata": {"word_count": 1, "cost": 100},
                },
            )
        c = Nativ(api_key=API_KEY, base_url=BASE)
        results = c.translate_batch(["Sign up", "Log in"], "German")
        assert len(results) == 2


class TestBuildTranslateBody:
    def test_minimal(self):
        body = _build_translate_body("hello", "French")
        assert body["text"] == "hello"
        assert body["language"] == "French"
        assert body["tool"] == "api"
        assert "context" not in body

    def test_all_options(self):
        body = _build_translate_body(
            "hello", "French",
            target_language_code="fr",
            context="button",
            glossary="a,b",
            formality="formal",
            max_characters=50,
        )
        assert body["language_code"] == "fr"
        assert body["context"] == "button"
        assert body["glossary"] == "a,b"
        assert body["formality"] == "formal"
        assert body["max_characters"] == 50


# ---------------------------------------------------------------------------
# OCR
# ---------------------------------------------------------------------------


class TestOCR:
    def test_extract_text(self, httpx_mock, tmp_path):
        httpx_mock.add_response(
            url=f"{BASE}/text/extract",
            method="POST",
            json={"extracted_text": "Hello from image"},
        )
        img = tmp_path / "test.png"
        img.write_bytes(b"\x89PNG fake")
        c = Nativ(api_key=API_KEY, base_url=BASE)
        result = c.extract_text(str(img))
        assert result.extracted_text == "Hello from image"

    def test_extract_text_bytes(self, httpx_mock):
        httpx_mock.add_response(
            url=f"{BASE}/text/extract",
            method="POST",
            json={"extracted_text": "bytes result"},
        )
        c = Nativ(api_key=API_KEY, base_url=BASE)
        result = c.extract_text(b"\x89PNG fake bytes")
        assert result.extracted_text == "bytes result"


# ---------------------------------------------------------------------------
# Image
# ---------------------------------------------------------------------------


class TestImage:
    def test_culturalize_image(self, httpx_mock, tmp_path):
        httpx_mock.add_response(
            url=f"{BASE}/image/culturalize",
            method="POST",
            json={
                "images": [{"image_base64": "abc123"}],
                "metadata": {"cost": 500, "num_images": 1},
            },
        )
        img = tmp_path / "ref.png"
        img.write_bytes(b"\x89PNG fake")
        c = Nativ(api_key=API_KEY, base_url=BASE)
        result = c.culturalize_image(str(img), text="Soldes", language_code="fr")
        assert len(result.images) == 1
        assert result.images[0].image_base64 == "abc123"
        assert result.metadata.cost == 500

    def test_inspect_image(self, httpx_mock, tmp_path):
        httpx_mock.add_response(
            url=f"{BASE}/image/inspect",
            method="POST",
            json={
                "verdict": "NOT SAFE",
                "affected_countries": [
                    {
                        "country": "Japan",
                        "issue": "Rising sun imagery",
                        "suggestion": "Remove symbol",
                    }
                ],
            },
        )
        img = tmp_path / "ad.jpg"
        img.write_bytes(b"\xff\xd8 fake jpeg")
        c = Nativ(api_key=API_KEY, base_url=BASE)
        result = c.inspect_image(str(img))
        assert result.verdict == "NOT SAFE"
        assert len(result.affected_countries) == 1
        assert result.affected_countries[0].country == "Japan"


# ---------------------------------------------------------------------------
# Languages
# ---------------------------------------------------------------------------


class TestLanguages:
    def test_get_languages(self, httpx_mock):
        httpx_mock.add_response(
            url=f"{BASE}/user/languages",
            method="GET",
            json={
                "languages": [
                    {"id": 1, "language": "French", "language_code": "fr", "formality": "formal"},
                    {"id": 2, "language": "German", "language_code": "de"},
                ]
            },
        )
        c = Nativ(api_key=API_KEY, base_url=BASE)
        langs = c.get_languages()
        assert len(langs) == 2
        assert langs[0].language == "French"
        assert langs[0].formality == "formal"
        assert langs[1].custom_style is None

    def test_update_formality(self, httpx_mock):
        httpx_mock.add_response(
            url=f"{BASE}/user/languages/1/formality",
            method="PATCH",
            json={"success": True},
        )
        c = Nativ(api_key=API_KEY, base_url=BASE)
        assert c.update_language_formality(1, "formal") is True

    def test_update_custom_style(self, httpx_mock):
        httpx_mock.add_response(
            url=f"{BASE}/user/languages/2/custom-style",
            method="PATCH",
            json={"success": True},
        )
        c = Nativ(api_key=API_KEY, base_url=BASE)
        assert c.update_language_custom_style(2, "Use du instead of Sie") is True


# ---------------------------------------------------------------------------
# Translation Memory
# ---------------------------------------------------------------------------


class TestTM:
    def test_search_tm(self, httpx_mock):
        httpx_mock.add_response(
            method="GET",
            json={
                "matches": [
                    {
                        "tm_id": "m1",
                        "score": 92.0,
                        "match_type": "fuzzy",
                        "source_text": "Sign up",
                        "target_text": "S'inscrire",
                        "information_source": "manual",
                    }
                ]
            },
        )
        c = Nativ(api_key=API_KEY, base_url=BASE)
        matches = c.search_tm("Sign up", target_language_code="fr")
        assert len(matches) == 1
        assert matches[0].score == 92.0

    def test_list_tm_entries(self, httpx_mock):
        httpx_mock.add_response(
            method="GET",
            json={
                "entries": [
                    {
                        "id": "e1",
                        "user_id": 1,
                        "source_language_code": "en",
                        "source_text": "Hello",
                        "target_language_code": "fr",
                        "target_text": "Bonjour",
                        "information_source": "manual",
                        "enabled": True,
                        "priority": 50,
                    }
                ],
                "total": 1,
                "offset": 0,
                "limit": 100,
            },
        )
        c = Nativ(api_key=API_KEY, base_url=BASE)
        result = c.list_tm_entries()
        assert result.total == 1
        assert result.entries[0].source_text == "Hello"

    def test_add_tm_entry(self, httpx_mock):
        httpx_mock.add_response(
            method="POST",
            json={
                "id": "new-1",
                "user_id": 1,
                "source_language_code": "en",
                "source_text": "Buy now",
                "target_language_code": "de",
                "target_text": "Jetzt kaufen",
                "information_source": "manual",
                "enabled": True,
                "priority": 50,
            },
        )
        c = Nativ(api_key=API_KEY, base_url=BASE)
        entry = c.add_tm_entry("Buy now", "Jetzt kaufen", "en", "de")
        assert entry.id == "new-1"
        assert entry.target_text == "Jetzt kaufen"

    def test_update_tm_entry(self, httpx_mock):
        httpx_mock.add_response(method="PATCH", json={"success": True})
        c = Nativ(api_key=API_KEY, base_url=BASE)
        assert c.update_tm_entry("e1", target_text="Salut") is True

    def test_update_tm_entry_no_fields(self):
        c = Nativ(api_key=API_KEY, base_url=BASE)
        with pytest.raises(ValidationError):
            c.update_tm_entry("e1")

    def test_delete_tm_entry(self, httpx_mock):
        httpx_mock.add_response(method="DELETE", json={"success": True})
        c = Nativ(api_key=API_KEY, base_url=BASE)
        assert c.delete_tm_entry("e1") is True

    def test_get_tm_stats(self, httpx_mock):
        httpx_mock.add_response(
            method="GET",
            json={"total": 500, "enabled": 480, "disabled": 20, "by_source": {"manual": {"total": 500}}},
        )
        c = Nativ(api_key=API_KEY, base_url=BASE)
        stats = c.get_tm_stats()
        assert stats.total == 500
        assert stats.enabled == 480


# ---------------------------------------------------------------------------
# Style Guides & Brand Voice
# ---------------------------------------------------------------------------


class TestStyleGuides:
    def test_get_style_guides(self, httpx_mock):
        httpx_mock.add_response(
            method="GET",
            json={
                "guides": [
                    {"id": "g1", "title": "Tone", "content": "Use active voice.", "is_enabled": True, "display_order": 0}
                ]
            },
        )
        c = Nativ(api_key=API_KEY, base_url=BASE)
        guides = c.get_style_guides()
        assert len(guides) == 1
        assert guides[0].title == "Tone"

    def test_create_style_guide(self, httpx_mock):
        httpx_mock.add_response(
            method="POST",
            json={"id": "g2", "title": "Brand", "content": "Be friendly.", "is_enabled": True, "display_order": 1},
        )
        c = Nativ(api_key=API_KEY, base_url=BASE)
        guide = c.create_style_guide("Brand", "Be friendly.")
        assert guide.id == "g2"

    def test_update_style_guide(self, httpx_mock):
        httpx_mock.add_response(
            method="PUT",
            json={"id": "g1", "title": "Tone v2", "content": "Use active voice.", "is_enabled": True, "display_order": 0},
        )
        c = Nativ(api_key=API_KEY, base_url=BASE)
        guide = c.update_style_guide("g1", title="Tone v2")
        assert guide.title == "Tone v2"

    def test_delete_style_guide(self, httpx_mock):
        httpx_mock.add_response(method="DELETE", json={"success": True})
        c = Nativ(api_key=API_KEY, base_url=BASE)
        assert c.delete_style_guide("g1") is True

    def test_get_brand_voice(self, httpx_mock):
        httpx_mock.add_response(
            method="GET",
            json={"prompt": "We are a friendly brand.", "exists": True, "cached": True},
        )
        c = Nativ(api_key=API_KEY, base_url=BASE)
        bv = c.get_brand_voice()
        assert bv.prompt == "We are a friendly brand."
        assert bv.exists is True


# ---------------------------------------------------------------------------
# Feedback
# ---------------------------------------------------------------------------


class TestFeedback:
    def test_submit_feedback(self, httpx_mock):
        httpx_mock.add_response(
            method="POST",
            json={"success": True, "message": "Saved", "feedback_id": "f1"},
        )
        c = Nativ(api_key=API_KEY, base_url=BASE)
        result = c.submit_feedback(source="Hello", result="Bonjour", approved=True)
        assert result["success"] is True


# ---------------------------------------------------------------------------
# Error handling
# ---------------------------------------------------------------------------


class TestErrors:
    @pytest.mark.parametrize(
        "status,exc_type",
        [
            (401, AuthenticationError),
            (402, InsufficientCreditsError),
            (404, NotFoundError),
            (429, RateLimitError),
            (400, ValidationError),
            (422, ValidationError),
            (500, ServerError),
            (503, ServerError),
        ],
    )
    def test_error_mapping(self, httpx_mock, status, exc_type):
        httpx_mock.add_response(
            url=f"{BASE}/text/culturalize",
            method="POST",
            status_code=status,
            json={"detail": "test error"},
        )
        c = Nativ(api_key=API_KEY, base_url=BASE)
        with pytest.raises(exc_type) as exc_info:
            c.translate("Hello", "French")
        assert exc_info.value.status_code == status
        assert exc_info.value.body is not None
