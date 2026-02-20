"""Unit tests for the asynchronous AsyncNativ client."""

import pytest

from nativ import AsyncNativ, AuthenticationError

API_KEY = "nativ_test_00000000000000000000000000000000"
BASE = "https://api.test.usenativ.com"


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
        "top_matches": [],
    },
    "rationale": "Chose formal register.",
}


@pytest.mark.anyio
class TestAsyncTranslate:
    async def test_translate(self, httpx_mock):
        httpx_mock.add_response(
            url=f"{BASE}/text/culturalize",
            method="POST",
            json=TRANSLATE_RESPONSE,
        )
        async with AsyncNativ(api_key=API_KEY, base_url=BASE) as c:
            result = await c.translate("Hello world", "French")
        assert result.translated_text == "Bonjour le monde"
        assert result.metadata.cost == 100

    async def test_translate_batch(self, httpx_mock):
        for _ in range(3):
            httpx_mock.add_response(
                url=f"{BASE}/text/culturalize",
                method="POST",
                json={
                    "translated_text": "translated",
                    "metadata": {"word_count": 1, "cost": 100},
                },
            )
        async with AsyncNativ(api_key=API_KEY, base_url=BASE) as c:
            results = await c.translate_batch(["a", "b", "c"], "Spanish")
        assert len(results) == 3


@pytest.mark.anyio
class TestAsyncOCR:
    async def test_extract_text(self, httpx_mock, tmp_path):
        httpx_mock.add_response(
            url=f"{BASE}/text/extract",
            method="POST",
            json={"extracted_text": "async OCR result"},
        )
        img = tmp_path / "test.png"
        img.write_bytes(b"\x89PNG fake")
        async with AsyncNativ(api_key=API_KEY, base_url=BASE) as c:
            result = await c.extract_text(str(img))
        assert result.extracted_text == "async OCR result"


@pytest.mark.anyio
class TestAsyncTM:
    async def test_search_tm(self, httpx_mock):
        httpx_mock.add_response(
            method="GET",
            json={
                "matches": [
                    {
                        "tm_id": "m1",
                        "score": 90.0,
                        "match_type": "fuzzy",
                        "source_text": "Hello",
                        "target_text": "Bonjour",
                        "information_source": "manual",
                    }
                ]
            },
        )
        async with AsyncNativ(api_key=API_KEY, base_url=BASE) as c:
            matches = await c.search_tm("Hello", target_language_code="fr")
        assert len(matches) == 1

    async def test_add_tm_entry(self, httpx_mock):
        httpx_mock.add_response(
            method="POST",
            json={
                "id": "new-async",
                "user_id": 1,
                "source_language_code": "en",
                "source_text": "Test",
                "target_language_code": "fr",
                "target_text": "Test",
                "information_source": "manual",
                "enabled": True,
                "priority": 50,
            },
        )
        async with AsyncNativ(api_key=API_KEY, base_url=BASE) as c:
            entry = await c.add_tm_entry("Test", "Test", "en", "fr")
        assert entry.id == "new-async"

    async def test_get_tm_stats(self, httpx_mock):
        httpx_mock.add_response(
            method="GET",
            json={"total": 100, "enabled": 90, "disabled": 10, "by_source": {}},
        )
        async with AsyncNativ(api_key=API_KEY, base_url=BASE) as c:
            stats = await c.get_tm_stats()
        assert stats.total == 100


@pytest.mark.anyio
class TestAsyncStyleGuides:
    async def test_get_style_guides(self, httpx_mock):
        httpx_mock.add_response(
            method="GET",
            json={
                "guides": [
                    {"id": "g1", "title": "Tone", "content": "Active voice.", "is_enabled": True}
                ]
            },
        )
        async with AsyncNativ(api_key=API_KEY, base_url=BASE) as c:
            guides = await c.get_style_guides()
        assert len(guides) == 1

    async def test_get_brand_voice(self, httpx_mock):
        httpx_mock.add_response(
            method="GET",
            json={"prompt": "Friendly brand.", "exists": True, "cached": False},
        )
        async with AsyncNativ(api_key=API_KEY, base_url=BASE) as c:
            bv = await c.get_brand_voice()
        assert bv.prompt == "Friendly brand."


@pytest.mark.anyio
class TestAsyncErrors:
    async def test_401(self, httpx_mock):
        httpx_mock.add_response(
            url=f"{BASE}/text/culturalize",
            method="POST",
            status_code=401,
            json={"detail": "Invalid API key"},
        )
        async with AsyncNativ(api_key=API_KEY, base_url=BASE) as c:
            with pytest.raises(AuthenticationError):
                await c.translate("Hello", "French")
