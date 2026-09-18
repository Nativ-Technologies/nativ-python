"""Nativ Python SDK — AI-powered localization.

Usage::

    from nativ import Nativ

    client = Nativ()  # reads NATIV_API_KEY from env
    result = client.translate("Hello world", target_language="French")
    print(result.translated_text)
"""

from ._version import __version__
from ._client import Nativ, AsyncNativ, FileInput
from ._exceptions import (
    NativError,
    AuthenticationError,
    InsufficientCreditsError,
    ValidationError,
    NotFoundError,
    RateLimitError,
    ServerError,
)
from ._types import (
    Translation,
    TranslationMetadata,
    TMMatch,
    TMMatchDetail,
    OCRResult,
    GeneratedImage,
    ImageMetadata,
    ImageResult,
    AffectedCountry,
    CulturalInspection,
    Language,
    TMEntry,
    TMEntryList,
    TMSearchMatch,
    TMStats,
    StyleGuide,
    BrandVoice,
)
from ._media import (
    AudioConsentScript,
    AudioPreview,
    AudioSegment,
    AudioSynthesis,
    AudioSynthesizeMetadata,
    AudioTranscript,
    AudioVoice,
    AudioVoices,
    ClonedVoice,
    RemuxedVideo,
    SubtitleCue,
    SubtitleParse,
    SubtitlePlayground,
    SubtitlePlaygroundCue,
    SubtitlePlaygroundLanguage,
)

__all__ = [
    "__version__",
    "Nativ",
    "AsyncNativ",
    "FileInput",
    "NativError",
    "AuthenticationError",
    "InsufficientCreditsError",
    "ValidationError",
    "NotFoundError",
    "RateLimitError",
    "ServerError",
    "Translation",
    "TranslationMetadata",
    "TMMatch",
    "TMMatchDetail",
    "OCRResult",
    "GeneratedImage",
    "ImageMetadata",
    "ImageResult",
    "AffectedCountry",
    "CulturalInspection",
    "Language",
    "TMEntry",
    "TMEntryList",
    "TMSearchMatch",
    "TMStats",
    "StyleGuide",
    "BrandVoice",
    "AudioSegment",
    "AudioTranscript",
    "AudioVoice",
    "AudioVoices",
    "AudioPreview",
    "AudioConsentScript",
    "ClonedVoice",
    "AudioSynthesizeMetadata",
    "AudioSynthesis",
    "RemuxedVideo",
    "SubtitleCue",
    "SubtitleParse",
    "SubtitlePlaygroundCue",
    "SubtitlePlaygroundLanguage",
    "SubtitlePlayground",
]
