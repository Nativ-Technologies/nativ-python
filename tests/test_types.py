"""Unit tests for response type parsing helpers."""

from nativ._types import (
    _parse_translation,
    _parse_tm_entry,
    _parse_style_guide,
    Translation,
    TMEntry,
    StyleGuide,
)


class TestParseTranslation:
    def test_full_response(self):
        data = {
            "translated_text": "Bonjour",
            "metadata": {"word_count": 1, "cost": 100},
            "tm_match": {
                "score": 100.0,
                "match_type": "exact",
                "source_text": "Hello",
                "target_text": "Bonjour",
                "tm_source": "manual",
                "tm_id": "x",
                "top_matches": [
                    {
                        "tm_id": "x",
                        "score": 100.0,
                        "match_type": "exact",
                        "source_text": "Hello",
                        "target_text": "Bonjour",
                        "information_source": "manual",
                    }
                ],
            },
            "rationale": "Exact match.",
            "backtranslation": "Hello",
        }
        t = _parse_translation(data)
        assert isinstance(t, Translation)
        assert t.translated_text == "Bonjour"
        assert t.metadata.word_count == 1
        assert t.tm_match is not None
        assert t.tm_match.score == 100.0
        assert len(t.tm_match.top_matches) == 1
        assert t.rationale == "Exact match."
        assert t.backtranslation == "Hello"

    def test_minimal_response(self):
        data = {"translated_text": "Hi", "metadata": {}}
        t = _parse_translation(data)
        assert t.translated_text == "Hi"
        assert t.metadata.word_count == 0
        assert t.tm_match is None
        assert t.rationale is None

    def test_zero_score_tm_ignored(self):
        data = {
            "translated_text": "X",
            "metadata": {"word_count": 1, "cost": 100},
            "tm_match": {"score": 0, "match_type": "none"},
        }
        t = _parse_translation(data)
        assert t.tm_match is None


class TestParseTMEntry:
    def test_full_entry(self):
        data = {
            "id": "abc",
            "user_id": 42,
            "source_language_code": "en",
            "source_text": "Buy",
            "target_language_code": "fr",
            "target_text": "Acheter",
            "information_source": "manual",
            "enabled": True,
            "priority": 80,
            "created_at": "2024-01-01T00:00:00",
        }
        e = _parse_tm_entry(data)
        assert isinstance(e, TMEntry)
        assert e.id == "abc"
        assert e.priority == 80
        assert e.created_at == "2024-01-01T00:00:00"

    def test_defaults(self):
        e = _parse_tm_entry({})
        assert e.id == ""
        assert e.enabled is True
        assert e.priority == 50


class TestParseStyleGuide:
    def test_full(self):
        data = {"id": 7, "title": "Tone", "content": "Be formal.", "is_enabled": True, "display_order": 2, "user_id": 1}
        g = _parse_style_guide(data)
        assert isinstance(g, StyleGuide)
        assert g.id == "7"
        assert g.title == "Tone"
        assert g.is_enabled is True
