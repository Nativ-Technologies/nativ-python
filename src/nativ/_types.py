"""Response types for the Nativ SDK.

All types are plain dataclasses — zero extra dependencies beyond the stdlib.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


# ---------------------------------------------------------------------------
# Translation
# ---------------------------------------------------------------------------


@dataclass
class TranslationMetadata:
    """Cost and word-count metadata attached to every translation."""

    word_count: int
    cost: int


@dataclass
class TMMatchDetail:
    """A single translation-memory match returned alongside a translation."""

    tm_id: str
    score: float
    match_type: str
    source_text: str
    target_text: str
    information_source: str
    source_name: str = ""


@dataclass
class TMMatch:
    """Best TM match info for a translation."""

    score: float
    match_type: str
    source_text: Optional[str] = None
    target_text: Optional[str] = None
    tm_source: Optional[str] = None
    tm_source_name: Optional[str] = None
    tm_id: Optional[str] = None
    top_matches: List[TMMatchDetail] = field(default_factory=list)


@dataclass
class Translation:
    """Result of a translate call."""

    translated_text: str
    metadata: TranslationMetadata
    tm_match: Optional[TMMatch] = None
    rationale: Optional[str] = None
    backtranslation: Optional[str] = None


# ---------------------------------------------------------------------------
# OCR
# ---------------------------------------------------------------------------


@dataclass
class OCRResult:
    """Result of text extraction from an image."""

    extracted_text: str


# ---------------------------------------------------------------------------
# Image
# ---------------------------------------------------------------------------


@dataclass
class GeneratedImage:
    """A single generated image (base64-encoded)."""

    image_base64: str


@dataclass
class ImageMetadata:
    """Cost metadata for image generation."""

    cost: int
    num_images: int


@dataclass
class ImageResult:
    """Result of an image culturalization call."""

    images: List[GeneratedImage]
    metadata: ImageMetadata


@dataclass
class AffectedCountry:
    """A country flagged during cultural sensitivity inspection."""

    country: str
    issue: str
    suggestion: str


@dataclass
class CulturalInspection:
    """Result of a cultural sensitivity inspection."""

    verdict: str
    affected_countries: List[AffectedCountry]


# ---------------------------------------------------------------------------
# Languages
# ---------------------------------------------------------------------------


@dataclass
class Language:
    """A language configured in the Nativ workspace."""

    id: int
    language: str
    language_code: str
    formality: Optional[str] = None
    custom_style: Optional[str] = None


# ---------------------------------------------------------------------------
# Translation Memory
# ---------------------------------------------------------------------------


@dataclass
class TMEntry:
    """A single entry in the translation memory."""

    id: str
    source_language_code: str
    source_text: str
    target_language_code: str
    target_text: str
    information_source: str
    enabled: bool
    priority: int
    user_id: int = 0
    end_user_id: Optional[str] = None
    source_name: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    match_score: Optional[float] = None


@dataclass
class TMEntryList:
    """Paginated list of TM entries."""

    entries: List[TMEntry]
    total: int
    offset: int
    limit: int


@dataclass
class TMSearchMatch:
    """A fuzzy-search match from the translation memory."""

    tm_id: str
    score: float
    match_type: str
    source_text: str
    target_text: str
    information_source: str
    source_name: Optional[str] = None


@dataclass
class TMStats:
    """Translation memory statistics."""

    total: int
    enabled: int
    disabled: int
    by_source: Dict[str, Dict[str, int]] = field(default_factory=dict)


# ---------------------------------------------------------------------------
# Style Guides & Brand Voice
# ---------------------------------------------------------------------------


@dataclass
class StyleGuide:
    """A user-created style guide."""

    id: str
    title: str
    content: str
    is_enabled: bool
    display_order: int = 0
    user_id: Optional[int] = None


@dataclass
class BrandVoice:
    """The workspace brand-voice prompt."""

    prompt: Optional[str]
    exists: bool
    cached: bool = False


# ---------------------------------------------------------------------------
# Parsing helpers (used by _client.py)
# ---------------------------------------------------------------------------


def _parse_translation(data: Dict[str, Any]) -> Translation:
    meta_raw = data.get("metadata", {})
    metadata = TranslationMetadata(
        word_count=meta_raw.get("word_count", 0),
        cost=meta_raw.get("cost", 0),
    )

    tm_match: Optional[TMMatch] = None
    tm_raw = data.get("tm_match")
    if tm_raw and tm_raw.get("score", 0) > 0:
        top = [
            TMMatchDetail(
                tm_id=m.get("tm_id", ""),
                score=m.get("score", 0),
                match_type=m.get("match_type", ""),
                source_text=m.get("source_text", ""),
                target_text=m.get("target_text", ""),
                information_source=m.get("information_source", ""),
                source_name=m.get("source_name", ""),
            )
            for m in tm_raw.get("top_matches", [])
        ]
        tm_match = TMMatch(
            score=tm_raw.get("score", 0),
            match_type=tm_raw.get("match_type", ""),
            source_text=tm_raw.get("source_text"),
            target_text=tm_raw.get("target_text"),
            tm_source=tm_raw.get("tm_source"),
            tm_source_name=tm_raw.get("tm_source_name"),
            tm_id=tm_raw.get("tm_id"),
            top_matches=top,
        )

    return Translation(
        translated_text=data.get("translated_text", ""),
        metadata=metadata,
        tm_match=tm_match,
        rationale=data.get("rationale"),
        backtranslation=data.get("backtranslation"),
    )


def _parse_tm_entry(data: Dict[str, Any]) -> TMEntry:
    return TMEntry(
        id=data.get("id", ""),
        user_id=data.get("user_id", 0),
        end_user_id=data.get("end_user_id"),
        source_language_code=data.get("source_language_code", ""),
        source_text=data.get("source_text", ""),
        target_language_code=data.get("target_language_code", ""),
        target_text=data.get("target_text", ""),
        information_source=data.get("information_source", ""),
        source_name=data.get("source_name"),
        enabled=data.get("enabled", True),
        priority=data.get("priority", 50),
        created_at=data.get("created_at"),
        updated_at=data.get("updated_at"),
        match_score=data.get("match_score"),
    )


def _parse_style_guide(data: Dict[str, Any]) -> StyleGuide:
    return StyleGuide(
        id=str(data.get("id", "")),
        title=data.get("title", ""),
        content=data.get("content", ""),
        is_enabled=data.get("is_enabled", True),
        display_order=data.get("display_order", 0),
        user_id=data.get("user_id"),
    )
