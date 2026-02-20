"""Synchronous and asynchronous Nativ API clients."""

from __future__ import annotations

import mimetypes
import os
from pathlib import Path
from typing import Any, BinaryIO, Dict, List, Optional, Sequence, Union

import httpx

from ._exceptions import (
    AuthenticationError,
    InsufficientCreditsError,
    NativError,
    NotFoundError,
    RateLimitError,
    ServerError,
    ValidationError,
)
from ._types import (
    AffectedCountry,
    BrandVoice,
    CulturalInspection,
    GeneratedImage,
    ImageMetadata,
    ImageResult,
    Language,
    OCRResult,
    StyleGuide,
    TMEntry,
    TMEntryList,
    TMSearchMatch,
    TMStats,
    Translation,
    _parse_style_guide,
    _parse_tm_entry,
    _parse_translation,
)
from ._version import __version__

DEFAULT_BASE_URL = "https://api.usenativ.com"

FileInput = Union[str, Path, bytes, BinaryIO]


def _resolve_api_key(api_key: Optional[str]) -> str:
    key = api_key or os.environ.get("NATIV_API_KEY")
    if not key:
        raise AuthenticationError(
            "No API key provided. Pass api_key= or set the NATIV_API_KEY "
            "environment variable. Create one at "
            "https://dashboard.usenativ.com -> Settings -> API Keys"
        )
    return key


def _default_headers(api_key: str) -> Dict[str, str]:
    return {
        "X-API-Key": api_key,
        "User-Agent": f"nativ-python/{__version__}",
    }


def _prepare_file(file_input: FileInput) -> tuple:
    if isinstance(file_input, (str, Path)):
        path = Path(file_input)
        data = path.read_bytes()
        ct = mimetypes.guess_type(str(path))[0] or "application/octet-stream"
        return (path.name, data, ct)
    elif isinstance(file_input, bytes):
        return ("image.png", file_input, "image/png")
    else:
        data = file_input.read()
        name = getattr(file_input, "name", "image.png")
        ct = mimetypes.guess_type(name)[0] or "application/octet-stream"
        return (Path(name).name, data, ct)


def _raise_for_status(resp: httpx.Response) -> None:
    if resp.is_success:
        return
    try:
        body = resp.json()
    except Exception:
        body = {"detail": resp.text}
    detail = body.get("detail", resp.text)
    msg = f"{detail}" if detail else f"HTTP {resp.status_code}"
    exc_map = {
        401: AuthenticationError,
        402: InsufficientCreditsError,
        404: NotFoundError,
        429: RateLimitError,
    }
    if resp.status_code in exc_map:
        raise exc_map[resp.status_code](msg, status_code=resp.status_code, body=body)
    if 400 <= resp.status_code < 500:
        raise ValidationError(msg, status_code=resp.status_code, body=body)
    raise ServerError(msg, status_code=resp.status_code, body=body)


def _build_translate_body(
    text: str,
    target_language: str,
    *,
    target_language_code: Optional[str] = None,
    source_language: str = "English",
    source_language_code: str = "en",
    context: Optional[str] = None,
    glossary: Optional[str] = None,
    formality: Optional[str] = None,
    max_characters: Optional[int] = None,
    include_tm_info: bool = True,
    backtranslate: bool = False,
    include_rationale: bool = True,
) -> Dict[str, Any]:
    body: Dict[str, Any] = {
        "text": text,
        "language": target_language,
        "source_language": source_language,
        "source_language_code": source_language_code,
        "tool": "api",
        "include_tm_info": include_tm_info,
        "backtranslate": backtranslate,
        "include_rationale": include_rationale,
    }
    if target_language_code:
        body["language_code"] = target_language_code
    if context:
        body["context"] = context
    if glossary:
        body["glossary"] = glossary
    if formality:
        body["formality"] = formality
    if max_characters is not None:
        body["max_characters"] = max_characters
    return body


def _parse_image_result(data: Dict[str, Any]) -> ImageResult:
    images = [GeneratedImage(image_base64=img["image_base64"]) for img in data.get("images", [])]
    meta_raw = data.get("metadata", {})
    metadata = ImageMetadata(cost=meta_raw.get("cost", 0), num_images=meta_raw.get("num_images", 0))
    return ImageResult(images=images, metadata=metadata)


def _parse_inspection(data: Dict[str, Any]) -> CulturalInspection:
    affected = [
        AffectedCountry(country=c["country"], issue=c["issue"], suggestion=c["suggestion"])
        for c in data.get("affected_countries", [])
    ]
    return CulturalInspection(verdict=data.get("verdict", "SAFE"), affected_countries=affected)


def _parse_languages(data: Dict[str, Any]) -> List[Language]:
    return [
        Language(
            id=lang["id"],
            language=lang["language"],
            language_code=lang["language_code"],
            formality=lang.get("formality"),
            custom_style=lang.get("custom_style"),
        )
        for lang in data.get("languages", [])
    ]


def _parse_tm_search(data: Dict[str, Any]) -> List[TMSearchMatch]:
    return [
        TMSearchMatch(
            tm_id=m.get("tm_id", ""),
            score=m.get("score", 0),
            match_type=m.get("match_type", ""),
            source_text=m.get("source_text", ""),
            target_text=m.get("target_text", ""),
            information_source=m.get("information_source", ""),
            source_name=m.get("source_name"),
        )
        for m in data.get("matches", [])
    ]


def _parse_tm_list(data: Dict[str, Any], offset: int, limit: int) -> TMEntryList:
    entries = [_parse_tm_entry(e) for e in data.get("entries", [])]
    return TMEntryList(
        entries=entries,
        total=data.get("total", len(entries)),
        offset=data.get("offset", offset),
        limit=data.get("limit", limit),
    )


def _parse_tm_stats(data: Dict[str, Any]) -> TMStats:
    return TMStats(
        total=data.get("total", 0),
        enabled=data.get("enabled", 0),
        disabled=data.get("disabled", 0),
        by_source=data.get("by_source", {}),
    )


def _parse_brand_voice(data: Dict[str, Any]) -> BrandVoice:
    return BrandVoice(
        prompt=data.get("prompt"),
        exists=data.get("exists", False),
        cached=data.get("cached", False),
    )


# ===================================================================
# Synchronous client
# ===================================================================


class Nativ:
    """Synchronous Nativ API client.

    Usage::

        from nativ import Nativ

        client = Nativ(api_key="nativ_...")
        result = client.translate("Hello world", target_language="French")
        print(result.translated_text)
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        *,
        base_url: Optional[str] = None,
        timeout: float = 120.0,
    ) -> None:
        self._api_key = _resolve_api_key(api_key)
        self._base_url = (
            base_url or os.environ.get("NATIV_API_URL") or DEFAULT_BASE_URL
        ).rstrip("/")
        self._client = httpx.Client(
            base_url=self._base_url,
            headers=_default_headers(self._api_key),
            timeout=timeout,
        )

    def close(self) -> None:
        """Release underlying HTTP connection pool."""
        self._client.close()

    def __enter__(self) -> "Nativ":
        return self

    def __exit__(self, *args: Any) -> None:
        self.close()

    def _request(
        self,
        method: str,
        path: str,
        *,
        json: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
        data: Optional[Dict[str, Any]] = None,
        files: Optional[Any] = None,
    ) -> Dict[str, Any]:
        resp = self._client.request(
            method, path, json=json, params=params, data=data, files=files,
        )
        _raise_for_status(resp)
        return resp.json()

    # -- Translation -----------------------------------------------------

    def translate(
        self,
        text: str,
        target_language: str,
        *,
        target_language_code: Optional[str] = None,
        source_language: str = "English",
        source_language_code: str = "en",
        context: Optional[str] = None,
        glossary: Optional[str] = None,
        formality: Optional[str] = None,
        max_characters: Optional[int] = None,
        include_tm_info: bool = True,
        backtranslate: bool = False,
        include_rationale: bool = True,
    ) -> Translation:
        """Translate text with cultural adaptation.

        Uses your translation memory, brand voice, and style guides
        automatically.

        Args:
            text: The text to translate.
            target_language: Full language name (e.g. ``"French"``).
            target_language_code: ISO code (e.g. ``"fr"``). Auto-detected if omitted.
            source_language: Source language name. Defaults to ``"English"``.
            source_language_code: Source language code. Defaults to ``"en"``.
            context: Context hint (e.g. ``"mobile app button"``).
            glossary: Inline glossary (``"term,translation\nbrand,marque"``).
            formality: ``very_informal`` | ``informal`` | ``neutral`` |
                ``formal`` | ``very_formal``.
            max_characters: Strict character limit for the output.
            include_tm_info: Return TM match details (default ``True``).
            backtranslate: Return a back-translation (default ``False``).
            include_rationale: Return AI rationale (default ``True``).
        """
        body = _build_translate_body(
            text, target_language,
            target_language_code=target_language_code,
            source_language=source_language,
            source_language_code=source_language_code,
            context=context, glossary=glossary, formality=formality,
            max_characters=max_characters, include_tm_info=include_tm_info,
            backtranslate=backtranslate, include_rationale=include_rationale,
        )
        return _parse_translation(self._request("POST", "/text/culturalize", json=body))

    def translate_batch(
        self,
        texts: Sequence[str],
        target_language: str,
        *,
        target_language_code: Optional[str] = None,
        source_language: str = "English",
        source_language_code: str = "en",
        context: Optional[str] = None,
        formality: Optional[str] = None,
    ) -> List[Translation]:
        """Translate multiple texts to a single target language.

        Each text is translated individually using your TM and style guides.
        """
        return [
            self.translate(
                t, target_language,
                target_language_code=target_language_code,
                source_language=source_language,
                source_language_code=source_language_code,
                context=context, formality=formality,
                include_tm_info=True, backtranslate=False, include_rationale=False,
            )
            for t in texts
        ]

    # -- OCR -------------------------------------------------------------

    def extract_text(self, image: FileInput) -> OCRResult:
        """Extract text from an image using AI-powered OCR.

        Args:
            image: Path (str/Path), raw bytes, or file-like object.
                Supports JPEG, PNG, and WebP.
        """
        fn, fb, ct = _prepare_file(image)
        data = self._request("POST", "/text/extract", files={"file": (fn, fb, ct)})
        return OCRResult(extracted_text=data.get("extracted_text", ""))

    # -- Image -----------------------------------------------------------

    def culturalize_image(
        self,
        image: FileInput,
        text: str,
        language_code: str,
        *,
        output_format: str = "png",
        model: str = "gpt",
        num_images: int = 1,
    ) -> ImageResult:
        """Generate a styled text image from a reference.

        Args:
            image: Reference image file.
            text: Text to render (max 200 characters).
            language_code: Language code of the text (e.g. ``"fr"``).
            output_format: ``"png"`` | ``"jpeg"`` | ``"webp"``.
            model: ``"gpt"`` or ``"gemini"``.
            num_images: Variants to generate (1-5).
        """
        fn, fb, ct = _prepare_file(image)
        data = self._request(
            "POST", "/image/culturalize",
            files={"file": (fn, fb, ct)},
            data={"text": text, "language_code": language_code,
                  "output_format": output_format, "model": model,
                  "num_images": str(num_images), "tool": "api"},
        )
        return _parse_image_result(data)

    def inspect_image(
        self, image: FileInput, *, countries: Optional[List[str]] = None,
    ) -> CulturalInspection:
        """Check an image for cultural sensitivity issues.

        Args:
            image: Image to analyze.
            countries: Countries to check. Defaults to top 30 by GDP.
        """
        fn, fb, ct = _prepare_file(image)
        form: Dict[str, Any] = {}
        if countries:
            form["countries"] = ",".join(countries)
        data = self._request(
            "POST", "/image/inspect",
            files={"file": (fn, fb, ct)},
            data=form if form else None,
        )
        return _parse_inspection(data)

    # -- Languages -------------------------------------------------------

    def get_languages(self) -> List[Language]:
        """Get all languages configured for this workspace."""
        return _parse_languages(self._request("GET", "/user/languages"))

    def update_language_formality(self, mapping_id: int, formality: str) -> bool:
        """Update the formality setting for a language."""
        data = self._request("PATCH", f"/user/languages/{mapping_id}/formality", json={"formality": formality})
        return data.get("success", False)

    def update_language_custom_style(self, mapping_id: int, custom_style: Optional[str]) -> bool:
        """Update per-language custom style directives."""
        data = self._request("PATCH", f"/user/languages/{mapping_id}/custom-style", json={"custom_style": custom_style})
        return data.get("success", False)

    # -- Translation Memory ----------------------------------------------

    def search_tm(
        self, query: str, *,
        source_language_code: str = "en",
        target_language_code: Optional[str] = None,
        min_score: float = 0.0,
        limit: int = 10,
    ) -> List[TMSearchMatch]:
        """Fuzzy-search the translation memory.

        Args:
            query: Text to search for.
            source_language_code: Source language code (default ``"en"``).
            target_language_code: Filter by target language.
            min_score: Minimum match score 0-100.
            limit: Max results.
        """
        params: Dict[str, Any] = {"query": query, "source_lang": source_language_code, "score_cutoff": min_score, "limit": limit}
        if target_language_code:
            params["target_lang"] = target_language_code
        return _parse_tm_search(self._request("GET", "/master-tm/fuzzy-search", params=params))

    def list_tm_entries(
        self, *,
        source_language_code: Optional[str] = None,
        target_language_code: Optional[str] = None,
        information_source: Optional[str] = None,
        search: Optional[str] = None,
        enabled_only: bool = False,
        limit: int = 100,
        offset: int = 0,
    ) -> TMEntryList:
        """List translation memory entries with optional filters."""
        params: Dict[str, Any] = {"limit": limit, "offset": offset}
        if source_language_code:
            params["source_lang"] = source_language_code
        if target_language_code:
            params["target_lang"] = target_language_code
        if information_source:
            params["information_source"] = information_source
        if search:
            params["search"] = search
        if enabled_only:
            params["enabled_only"] = True
        return _parse_tm_list(self._request("GET", "/master-tm/entries", params=params), offset, limit)

    def add_tm_entry(
        self, source_text: str, target_text: str,
        source_language_code: str, target_language_code: str,
        *, name: Optional[str] = None,
    ) -> TMEntry:
        """Add an entry to the translation memory.

        Args:
            source_text: Original text.
            target_text: Approved translation.
            source_language_code: e.g. ``"en"``.
            target_language_code: e.g. ``"fr-FR"``.
            name: Optional label (e.g. ``"homepage hero"``).
        """
        body: Dict[str, Any] = {
            "source_text": source_text, "target_text": target_text,
            "source_language_code": source_language_code,
            "target_language_code": target_language_code,
            "information_source": "manual",
        }
        if name:
            body["source_name"] = name
        return _parse_tm_entry(self._request("POST", "/master-tm/entries", json=body))

    def update_tm_entry(self, entry_id: str, *, target_text: Optional[str] = None, enabled: Optional[bool] = None) -> bool:
        """Update an existing TM entry."""
        body: Dict[str, Any] = {}
        if target_text is not None:
            body["target_text"] = target_text
        if enabled is not None:
            body["enabled"] = enabled
        if not body:
            raise ValidationError("Provide at least one of target_text or enabled")
        return self._request("PATCH", f"/master-tm/entries/{entry_id}", json=body).get("success", False)

    def delete_tm_entry(self, entry_id: str) -> bool:
        """Delete a TM entry."""
        return self._request("DELETE", f"/master-tm/entries/{entry_id}").get("success", False)

    def get_tm_stats(self) -> TMStats:
        """Get translation memory statistics."""
        return _parse_tm_stats(self._request("GET", "/master-tm/stats"))

    # -- Style Guides & Brand Voice --------------------------------------

    def get_style_guides(self) -> List[StyleGuide]:
        """Get all style guides for this workspace."""
        return [_parse_style_guide(g) for g in self._request("GET", "/style-guide").get("guides", [])]

    def create_style_guide(self, title: str, content: str, *, is_enabled: bool = True) -> StyleGuide:
        """Create a new style guide."""
        return _parse_style_guide(self._request("POST", "/style-guide", json={"title": title, "content": content, "is_enabled": is_enabled}))

    def update_style_guide(self, guide_id: str, *, title: Optional[str] = None, content: Optional[str] = None, is_enabled: Optional[bool] = None) -> StyleGuide:
        """Update an existing style guide."""
        body: Dict[str, Any] = {}
        if title is not None:
            body["title"] = title
        if content is not None:
            body["content"] = content
        if is_enabled is not None:
            body["is_enabled"] = is_enabled
        return _parse_style_guide(self._request("PUT", f"/style-guide/{guide_id}", json=body))

    def delete_style_guide(self, guide_id: str) -> bool:
        """Delete a style guide."""
        return self._request("DELETE", f"/style-guide/{guide_id}").get("success", False)

    def get_brand_voice(self) -> BrandVoice:
        """Get the brand voice prompt."""
        return _parse_brand_voice(self._request("GET", "/style-guide/prompt"))

    def get_combined_prompt(self) -> Dict[str, Any]:
        """Get the combined prompt (brand voice + enabled style guides)."""
        return self._request("GET", "/style-guide/combined")

    # -- Feedback --------------------------------------------------------

    def submit_feedback(
        self, *, source: Optional[str] = None, result: Optional[str] = None,
        language: Optional[str] = None, feedback: Optional[str] = None,
        approved: Optional[bool] = None,
    ) -> Dict[str, Any]:
        """Submit feedback about a translation."""
        body: Dict[str, Any] = {}
        if source is not None:
            body["source"] = source
        if result is not None:
            body["result"] = result
        if language is not None:
            body["language"] = language
        if feedback is not None:
            body["feedback"] = feedback
        if approved is not None:
            body["approved"] = approved
        return self._request("POST", "/text/feedback", json=body)


# ===================================================================
# Asynchronous client
# ===================================================================


class AsyncNativ:
    """Asynchronous Nativ API client.

    Usage::

        import asyncio
        from nativ import AsyncNativ

        async def main():
            async with AsyncNativ(api_key="nativ_...") as client:
                result = await client.translate("Hello", target_language="French")
                print(result.translated_text)

        asyncio.run(main())
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        *,
        base_url: Optional[str] = None,
        timeout: float = 120.0,
    ) -> None:
        self._api_key = _resolve_api_key(api_key)
        self._base_url = (
            base_url or os.environ.get("NATIV_API_URL") or DEFAULT_BASE_URL
        ).rstrip("/")
        self._client = httpx.AsyncClient(
            base_url=self._base_url,
            headers=_default_headers(self._api_key),
            timeout=timeout,
        )

    async def close(self) -> None:
        """Release underlying HTTP connection pool."""
        await self._client.aclose()

    async def __aenter__(self) -> "AsyncNativ":
        return self

    async def __aexit__(self, *args: Any) -> None:
        await self.close()

    async def _request(
        self, method: str, path: str, *,
        json: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
        data: Optional[Dict[str, Any]] = None,
        files: Optional[Any] = None,
    ) -> Dict[str, Any]:
        resp = await self._client.request(
            method, path, json=json, params=params, data=data, files=files,
        )
        _raise_for_status(resp)
        return resp.json()

    # -- Translation -----------------------------------------------------

    async def translate(
        self, text: str, target_language: str, *,
        target_language_code: Optional[str] = None,
        source_language: str = "English",
        source_language_code: str = "en",
        context: Optional[str] = None,
        glossary: Optional[str] = None,
        formality: Optional[str] = None,
        max_characters: Optional[int] = None,
        include_tm_info: bool = True,
        backtranslate: bool = False,
        include_rationale: bool = True,
    ) -> Translation:
        """Translate text with cultural adaptation. See :meth:`Nativ.translate`."""
        body = _build_translate_body(
            text, target_language,
            target_language_code=target_language_code,
            source_language=source_language,
            source_language_code=source_language_code,
            context=context, glossary=glossary, formality=formality,
            max_characters=max_characters, include_tm_info=include_tm_info,
            backtranslate=backtranslate, include_rationale=include_rationale,
        )
        return _parse_translation(await self._request("POST", "/text/culturalize", json=body))

    async def translate_batch(
        self, texts: Sequence[str], target_language: str, *,
        target_language_code: Optional[str] = None,
        source_language: str = "English",
        source_language_code: str = "en",
        context: Optional[str] = None,
        formality: Optional[str] = None,
    ) -> List[Translation]:
        """Translate multiple texts. See :meth:`Nativ.translate_batch`."""
        return [
            await self.translate(
                t, target_language,
                target_language_code=target_language_code,
                source_language=source_language,
                source_language_code=source_language_code,
                context=context, formality=formality,
                include_tm_info=True, backtranslate=False, include_rationale=False,
            )
            for t in texts
        ]

    # -- OCR -------------------------------------------------------------

    async def extract_text(self, image: FileInput) -> OCRResult:
        """Extract text from an image. See :meth:`Nativ.extract_text`."""
        fn, fb, ct = _prepare_file(image)
        data = await self._request("POST", "/text/extract", files={"file": (fn, fb, ct)})
        return OCRResult(extracted_text=data.get("extracted_text", ""))

    # -- Image -----------------------------------------------------------

    async def culturalize_image(
        self, image: FileInput, text: str, language_code: str, *,
        output_format: str = "png", model: str = "gpt", num_images: int = 1,
    ) -> ImageResult:
        """Generate styled text image. See :meth:`Nativ.culturalize_image`."""
        fn, fb, ct = _prepare_file(image)
        data = await self._request(
            "POST", "/image/culturalize",
            files={"file": (fn, fb, ct)},
            data={"text": text, "language_code": language_code,
                  "output_format": output_format, "model": model,
                  "num_images": str(num_images), "tool": "api"},
        )
        return _parse_image_result(data)

    async def inspect_image(
        self, image: FileInput, *, countries: Optional[List[str]] = None,
    ) -> CulturalInspection:
        """Cultural sensitivity check. See :meth:`Nativ.inspect_image`."""
        fn, fb, ct = _prepare_file(image)
        form: Dict[str, Any] = {}
        if countries:
            form["countries"] = ",".join(countries)
        data = await self._request(
            "POST", "/image/inspect",
            files={"file": (fn, fb, ct)},
            data=form if form else None,
        )
        return _parse_inspection(data)

    # -- Languages -------------------------------------------------------

    async def get_languages(self) -> List[Language]:
        """Get configured languages. See :meth:`Nativ.get_languages`."""
        return _parse_languages(await self._request("GET", "/user/languages"))

    async def update_language_formality(self, mapping_id: int, formality: str) -> bool:
        """Update language formality. See :meth:`Nativ.update_language_formality`."""
        data = await self._request("PATCH", f"/user/languages/{mapping_id}/formality", json={"formality": formality})
        return data.get("success", False)

    async def update_language_custom_style(self, mapping_id: int, custom_style: Optional[str]) -> bool:
        """Update custom style. See :meth:`Nativ.update_language_custom_style`."""
        data = await self._request("PATCH", f"/user/languages/{mapping_id}/custom-style", json={"custom_style": custom_style})
        return data.get("success", False)

    # -- Translation Memory ----------------------------------------------

    async def search_tm(
        self, query: str, *,
        source_language_code: str = "en",
        target_language_code: Optional[str] = None,
        min_score: float = 0.0,
        limit: int = 10,
    ) -> List[TMSearchMatch]:
        """Fuzzy-search the TM. See :meth:`Nativ.search_tm`."""
        params: Dict[str, Any] = {"query": query, "source_lang": source_language_code, "score_cutoff": min_score, "limit": limit}
        if target_language_code:
            params["target_lang"] = target_language_code
        return _parse_tm_search(await self._request("GET", "/master-tm/fuzzy-search", params=params))

    async def list_tm_entries(
        self, *,
        source_language_code: Optional[str] = None,
        target_language_code: Optional[str] = None,
        information_source: Optional[str] = None,
        search: Optional[str] = None,
        enabled_only: bool = False,
        limit: int = 100,
        offset: int = 0,
    ) -> TMEntryList:
        """List TM entries. See :meth:`Nativ.list_tm_entries`."""
        params: Dict[str, Any] = {"limit": limit, "offset": offset}
        if source_language_code:
            params["source_lang"] = source_language_code
        if target_language_code:
            params["target_lang"] = target_language_code
        if information_source:
            params["information_source"] = information_source
        if search:
            params["search"] = search
        if enabled_only:
            params["enabled_only"] = True
        return _parse_tm_list(await self._request("GET", "/master-tm/entries", params=params), offset, limit)

    async def add_tm_entry(
        self, source_text: str, target_text: str,
        source_language_code: str, target_language_code: str,
        *, name: Optional[str] = None,
    ) -> TMEntry:
        """Add a TM entry. See :meth:`Nativ.add_tm_entry`."""
        body: Dict[str, Any] = {
            "source_text": source_text, "target_text": target_text,
            "source_language_code": source_language_code,
            "target_language_code": target_language_code,
            "information_source": "manual",
        }
        if name:
            body["source_name"] = name
        return _parse_tm_entry(await self._request("POST", "/master-tm/entries", json=body))

    async def update_tm_entry(self, entry_id: str, *, target_text: Optional[str] = None, enabled: Optional[bool] = None) -> bool:
        """Update a TM entry. See :meth:`Nativ.update_tm_entry`."""
        body: Dict[str, Any] = {}
        if target_text is not None:
            body["target_text"] = target_text
        if enabled is not None:
            body["enabled"] = enabled
        if not body:
            raise ValidationError("Provide at least one of target_text or enabled")
        return (await self._request("PATCH", f"/master-tm/entries/{entry_id}", json=body)).get("success", False)

    async def delete_tm_entry(self, entry_id: str) -> bool:
        """Delete a TM entry. See :meth:`Nativ.delete_tm_entry`."""
        return (await self._request("DELETE", f"/master-tm/entries/{entry_id}")).get("success", False)

    async def get_tm_stats(self) -> TMStats:
        """Get TM statistics. See :meth:`Nativ.get_tm_stats`."""
        return _parse_tm_stats(await self._request("GET", "/master-tm/stats"))

    # -- Style Guides & Brand Voice --------------------------------------

    async def get_style_guides(self) -> List[StyleGuide]:
        """Get style guides. See :meth:`Nativ.get_style_guides`."""
        return [_parse_style_guide(g) for g in (await self._request("GET", "/style-guide")).get("guides", [])]

    async def create_style_guide(self, title: str, content: str, *, is_enabled: bool = True) -> StyleGuide:
        """Create a style guide. See :meth:`Nativ.create_style_guide`."""
        return _parse_style_guide(await self._request("POST", "/style-guide", json={"title": title, "content": content, "is_enabled": is_enabled}))

    async def update_style_guide(
        self, guide_id: str, *, title: Optional[str] = None,
        content: Optional[str] = None, is_enabled: Optional[bool] = None,
    ) -> StyleGuide:
        """Update a style guide. See :meth:`Nativ.update_style_guide`."""
        body: Dict[str, Any] = {}
        if title is not None:
            body["title"] = title
        if content is not None:
            body["content"] = content
        if is_enabled is not None:
            body["is_enabled"] = is_enabled
        return _parse_style_guide(await self._request("PUT", f"/style-guide/{guide_id}", json=body))

    async def delete_style_guide(self, guide_id: str) -> bool:
        """Delete a style guide. See :meth:`Nativ.delete_style_guide`."""
        return (await self._request("DELETE", f"/style-guide/{guide_id}")).get("success", False)

    async def get_brand_voice(self) -> BrandVoice:
        """Get brand voice. See :meth:`Nativ.get_brand_voice`."""
        return _parse_brand_voice(await self._request("GET", "/style-guide/prompt"))

    async def get_combined_prompt(self) -> Dict[str, Any]:
        """Get combined prompt. See :meth:`Nativ.get_combined_prompt`."""
        return await self._request("GET", "/style-guide/combined")

    # -- Feedback --------------------------------------------------------

    async def submit_feedback(
        self, *, source: Optional[str] = None, result: Optional[str] = None,
        language: Optional[str] = None, feedback: Optional[str] = None,
        approved: Optional[bool] = None,
    ) -> Dict[str, Any]:
        """Submit feedback. See :meth:`Nativ.submit_feedback`."""
        body: Dict[str, Any] = {}
        if source is not None:
            body["source"] = source
        if result is not None:
            body["result"] = result
        if language is not None:
            body["language"] = language
        if feedback is not None:
            body["feedback"] = feedback
        if approved is not None:
            body["approved"] = approved
        return await self._request("POST", "/text/feedback", json=body)
