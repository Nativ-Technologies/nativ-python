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

__all__ = [
    "__version__",
    # Clients
    "Nativ",
    "AsyncNativ",
    "FileInput",
    # Exceptions
    "NativError",
    "AuthenticationError",
    "InsufficientCreditsError",
    "ValidationError",
    "NotFoundError",
    "RateLimitError",
    "ServerError",
    # Response types
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
]
