"""Tests for the Nativ CLI."""

import json
from unittest.mock import patch, MagicMock

import pytest

from nativ._cli import main
from nativ._types import (
    Translation, TranslationMetadata, TMMatch, TMMatchDetail,
    Language, TMEntry, TMEntryList, TMSearchMatch, TMStats,
    StyleGuide, BrandVoice, OCRResult, CulturalInspection, AffectedCountry,
)

API_KEY = "nativ_test_00000000000000000000000000000000"


def _mock_client():
    """Return a MagicMock that acts like Nativ()."""
    m = MagicMock()
    m.close = MagicMock()
    return m


def _sample_translation(**overrides):
    defaults = dict(
        translated_text="Bonjour le monde",
        metadata=TranslationMetadata(word_count=3, cost=1),
        tm_match=None,
        rationale="Direct translation",
        backtranslation=None,
    )
    defaults.update(overrides)
    return Translation(**defaults)


# ---------------------------------------------------------------------------
# nativ --version
# ---------------------------------------------------------------------------

def test_version(capsys):
    with pytest.raises(SystemExit) as exc:
        main(["--version"])
    assert exc.value.code == 0
    out = capsys.readouterr().out
    assert "nativ" in out


# ---------------------------------------------------------------------------
# nativ (no command)
# ---------------------------------------------------------------------------

def test_no_command(capsys):
    rc = main([])
    assert rc == 0
    out = capsys.readouterr().out
    assert "usage" in out.lower() or "nativ" in out.lower()


# ---------------------------------------------------------------------------
# nativ translate
# ---------------------------------------------------------------------------

@patch("nativ._cli._get_client")
def test_translate_plain(mock_gc, capsys):
    client = _mock_client()
    client.translate.return_value = _sample_translation()
    mock_gc.return_value = client

    rc = main(["translate", "Hello world", "--to", "French"])
    assert rc == 0
    out = capsys.readouterr().out
    assert "Bonjour le monde" in out
    client.translate.assert_called_once()
    client.close.assert_called_once()


@patch("nativ._cli._get_client")
def test_translate_json(mock_gc, capsys):
    client = _mock_client()
    client.translate.return_value = _sample_translation()
    mock_gc.return_value = client

    rc = main(["translate", "Hello", "--to", "French", "--json"])
    assert rc == 0
    data = json.loads(capsys.readouterr().out)
    assert data["translated_text"] == "Bonjour le monde"


@patch("nativ._cli._get_client")
def test_translate_with_backtranslation(mock_gc, capsys):
    client = _mock_client()
    client.translate.return_value = _sample_translation(backtranslation="Hello the world")
    mock_gc.return_value = client

    rc = main(["translate", "Hello", "--to", "French", "--backtranslate"])
    assert rc == 0
    out = capsys.readouterr().out
    assert "Back-translation" in out
    assert "Hello the world" in out


@patch("nativ._cli._get_client")
def test_translate_with_tm_match(mock_gc, capsys):
    client = _mock_client()
    client.translate.return_value = _sample_translation(
        tm_match=TMMatch(score=95.0, match_type="fuzzy", top_matches=[])
    )
    mock_gc.return_value = client

    rc = main(["translate", "Hello", "--to", "French"])
    assert rc == 0
    out = capsys.readouterr().out
    assert "95%" in out


@patch("nativ._cli._get_client")
def test_translate_formality(mock_gc, capsys):
    client = _mock_client()
    client.translate.return_value = _sample_translation()
    mock_gc.return_value = client

    rc = main(["translate", "Hey", "--to", "French", "--formality", "formal"])
    assert rc == 0
    call_kwargs = client.translate.call_args
    assert call_kwargs[1]["formality"] == "formal"


# ---------------------------------------------------------------------------
# nativ batch
# ---------------------------------------------------------------------------

@patch("nativ._cli._get_client")
def test_batch_plain(mock_gc, capsys):
    client = _mock_client()
    client.translate_batch.return_value = [
        _sample_translation(translated_text="Bonjour"),
        _sample_translation(translated_text="Au revoir"),
    ]
    mock_gc.return_value = client

    rc = main(["batch", "Hello", "Goodbye", "--to", "French"])
    assert rc == 0
    out = capsys.readouterr().out
    assert "Bonjour" in out
    assert "Au revoir" in out


@patch("nativ._cli._get_client")
def test_batch_json(mock_gc, capsys):
    client = _mock_client()
    client.translate_batch.return_value = [
        _sample_translation(translated_text="Hola"),
    ]
    mock_gc.return_value = client

    rc = main(["batch", "Hello", "--to", "Spanish", "--json"])
    assert rc == 0
    data = json.loads(capsys.readouterr().out)
    assert isinstance(data, list)
    assert data[0]["translated_text"] == "Hola"


# ---------------------------------------------------------------------------
# nativ languages
# ---------------------------------------------------------------------------

@patch("nativ._cli._get_client")
def test_languages_plain(mock_gc, capsys):
    client = _mock_client()
    client.get_languages.return_value = [
        Language(id=1, language="French", language_code="fr", formality="formal"),
        Language(id=2, language="German", language_code="de"),
    ]
    mock_gc.return_value = client

    rc = main(["languages"])
    assert rc == 0
    out = capsys.readouterr().out
    assert "French (fr)" in out
    assert "formality=formal" in out
    assert "German (de)" in out


@patch("nativ._cli._get_client")
def test_languages_json(mock_gc, capsys):
    client = _mock_client()
    client.get_languages.return_value = [
        Language(id=1, language="French", language_code="fr"),
    ]
    mock_gc.return_value = client

    rc = main(["lang", "--json"])
    assert rc == 0
    data = json.loads(capsys.readouterr().out)
    assert data[0]["language"] == "French"


# ---------------------------------------------------------------------------
# nativ tm search
# ---------------------------------------------------------------------------

@patch("nativ._cli._get_client")
def test_tm_search(mock_gc, capsys):
    client = _mock_client()
    client.search_tm.return_value = [
        TMSearchMatch(tm_id="abc", score=92.0, match_type="fuzzy",
                      source_text="Hello", target_text="Bonjour",
                      information_source="manual"),
    ]
    mock_gc.return_value = client

    rc = main(["tm", "search", "Hello"])
    assert rc == 0
    out = capsys.readouterr().out
    assert "92%" in out
    assert "Bonjour" in out


@patch("nativ._cli._get_client")
def test_tm_search_no_results(mock_gc, capsys):
    client = _mock_client()
    client.search_tm.return_value = []
    mock_gc.return_value = client

    rc = main(["tm", "search", "xyzzy"])
    assert rc == 0
    out = capsys.readouterr().out
    assert "No matches" in out


# ---------------------------------------------------------------------------
# nativ tm list
# ---------------------------------------------------------------------------

@patch("nativ._cli._get_client")
def test_tm_list(mock_gc, capsys):
    client = _mock_client()
    client.list_tm_entries.return_value = TMEntryList(
        entries=[
            TMEntry(id="entry-001", source_language_code="en",
                    source_text="Hello", target_language_code="fr",
                    target_text="Bonjour", information_source="manual",
                    enabled=True, priority=50),
        ],
        total=1, offset=0, limit=20,
    )
    mock_gc.return_value = client

    rc = main(["tm", "list"])
    assert rc == 0
    out = capsys.readouterr().out
    assert "1 of 1" in out
    assert "Hello" in out


# ---------------------------------------------------------------------------
# nativ tm add
# ---------------------------------------------------------------------------

@patch("nativ._cli._get_client")
def test_tm_add(mock_gc, capsys):
    client = _mock_client()
    client.add_tm_entry.return_value = TMEntry(
        id="new-id", source_language_code="en", source_text="Hi",
        target_language_code="fr", target_text="Salut",
        information_source="manual", enabled=True, priority=50,
    )
    mock_gc.return_value = client

    rc = main(["tm", "add", "Hi", "Salut", "--source-lang", "en", "--target-lang", "fr"])
    assert rc == 0
    out = capsys.readouterr().out
    assert "Added" in out
    assert "Salut" in out


# ---------------------------------------------------------------------------
# nativ tm delete
# ---------------------------------------------------------------------------

@patch("nativ._cli._get_client")
def test_tm_delete(mock_gc, capsys):
    client = _mock_client()
    client.delete_tm_entry.return_value = True
    mock_gc.return_value = client

    rc = main(["tm", "delete", "entry-001"])
    assert rc == 0
    assert "Deleted" in capsys.readouterr().out


@patch("nativ._cli._get_client")
def test_tm_delete_fail(mock_gc, capsys):
    client = _mock_client()
    client.delete_tm_entry.return_value = False
    mock_gc.return_value = client

    rc = main(["tm", "delete", "entry-001"])
    assert rc == 1


# ---------------------------------------------------------------------------
# nativ tm stats
# ---------------------------------------------------------------------------

@patch("nativ._cli._get_client")
def test_tm_stats(mock_gc, capsys):
    client = _mock_client()
    client.get_tm_stats.return_value = TMStats(total=100, enabled=80, disabled=20)
    mock_gc.return_value = client

    rc = main(["tm", "stats"])
    assert rc == 0
    out = capsys.readouterr().out
    assert "100" in out
    assert "80" in out


@patch("nativ._cli._get_client")
def test_tm_stats_json(mock_gc, capsys):
    client = _mock_client()
    client.get_tm_stats.return_value = TMStats(total=50, enabled=40, disabled=10)
    mock_gc.return_value = client

    rc = main(["tm", "stats", "--json"])
    assert rc == 0
    data = json.loads(capsys.readouterr().out)
    assert data["total"] == 50


# ---------------------------------------------------------------------------
# nativ style-guides
# ---------------------------------------------------------------------------

@patch("nativ._cli._get_client")
def test_style_guides(mock_gc, capsys):
    client = _mock_client()
    client.get_style_guides.return_value = [
        StyleGuide(id="sg1", title="Tone", content="Be friendly.\nUse active voice.",
                   is_enabled=True, display_order=0),
    ]
    mock_gc.return_value = client

    rc = main(["style-guides"])
    assert rc == 0
    out = capsys.readouterr().out
    assert "Tone" in out
    assert "enabled" in out


@patch("nativ._cli._get_client")
def test_style_guides_empty(mock_gc, capsys):
    client = _mock_client()
    client.get_style_guides.return_value = []
    mock_gc.return_value = client

    rc = main(["sg"])
    assert rc == 0
    assert "No style guides" in capsys.readouterr().out


# ---------------------------------------------------------------------------
# nativ brand-voice
# ---------------------------------------------------------------------------

@patch("nativ._cli._get_client")
def test_brand_voice(mock_gc, capsys):
    client = _mock_client()
    client.get_brand_voice.return_value = BrandVoice(
        prompt="We are bold and friendly.", exists=True
    )
    mock_gc.return_value = client

    rc = main(["brand-voice"])
    assert rc == 0
    assert "bold and friendly" in capsys.readouterr().out


@patch("nativ._cli._get_client")
def test_brand_voice_empty(mock_gc, capsys):
    client = _mock_client()
    client.get_brand_voice.return_value = BrandVoice(prompt=None, exists=False)
    mock_gc.return_value = client

    rc = main(["bv"])
    assert rc == 0
    assert "No brand voice" in capsys.readouterr().out


# ---------------------------------------------------------------------------
# nativ extract
# ---------------------------------------------------------------------------

@patch("nativ._cli._get_client")
def test_extract(mock_gc, capsys):
    client = _mock_client()
    client.extract_text.return_value = OCRResult(extracted_text="Hello from image")
    mock_gc.return_value = client

    rc = main(["extract", "photo.png"])
    assert rc == 0
    assert "Hello from image" in capsys.readouterr().out


# ---------------------------------------------------------------------------
# nativ inspect
# ---------------------------------------------------------------------------

@patch("nativ._cli._get_client")
def test_inspect_safe(mock_gc, capsys):
    client = _mock_client()
    client.inspect_image.return_value = CulturalInspection(
        verdict="SAFE", affected_countries=[]
    )
    mock_gc.return_value = client

    rc = main(["inspect", "ad.jpg"])
    assert rc == 0
    assert "SAFE" in capsys.readouterr().out


@patch("nativ._cli._get_client")
def test_inspect_with_issues(mock_gc, capsys):
    client = _mock_client()
    client.inspect_image.return_value = CulturalInspection(
        verdict="NOT SAFE",
        affected_countries=[
            AffectedCountry(country="Japan", issue="Color issue",
                            suggestion="Use different palette"),
        ],
    )
    mock_gc.return_value = client

    rc = main(["inspect", "banner.png"])
    assert rc == 0
    out = capsys.readouterr().out
    assert "NOT SAFE" in out
    assert "Japan" in out
    assert "Color issue" in out


# ---------------------------------------------------------------------------
# Error handling
# ---------------------------------------------------------------------------

@patch("nativ._cli._get_client")
def test_api_error_caught(mock_gc, capsys):
    client = _mock_client()
    client.translate.side_effect = Exception("Connection refused")
    mock_gc.return_value = client

    rc = main(["translate", "Hi", "--to", "French"])
    assert rc == 1
    err = capsys.readouterr().err
    assert "Connection refused" in err


# ---------------------------------------------------------------------------
# Alias coverage
# ---------------------------------------------------------------------------

@patch("nativ._cli._get_client")
def test_translate_alias(mock_gc, capsys):
    client = _mock_client()
    client.translate.return_value = _sample_translation()
    mock_gc.return_value = client

    rc = main(["t", "Hey", "--to", "French"])
    assert rc == 0
    assert "Bonjour" in capsys.readouterr().out
