"""Audio, video, and subtitle API methods mixed into Nativ clients."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, BinaryIO, Dict, List, Optional, Sequence, TYPE_CHECKING, Union

FileInput = Union[str, Path, bytes, BinaryIO]


def _prep(file_input: FileInput, default_name: str = "upload.bin"):
    from ._client import _prepare_file
    return _prepare_file(file_input, default_name=default_name)

MEDIA_TIMEOUT = 300.0


@dataclass
class AudioSegment:
    id: str
    text: str
    start_ms: int = 0
    end_ms: int = 0


@dataclass
class AudioTranscript:
    transcript: str
    duration_ms: int
    segments: List[AudioSegment]
    provider: str
    estimated_credit_cost: int
    billed_seconds: int
    detected_language: Optional[str] = None
    stem_id: Optional[str] = None
    bed_mode: Optional[str] = None
    video_id: Optional[str] = None
    source_voice_audio_base64: Optional[str] = None


@dataclass
class AudioVoice:
    id: str
    name: str
    gender: str
    locale: str
    accent_label: str
    provider: str
    category: str = "preset"


@dataclass
class AudioVoices:
    voices: List[AudioVoice]
    provider: str


@dataclass
class AudioPreview:
    audio_base64: str
    mime_type: str
    duration_ms: int
    provider: str
    voice_id: str


@dataclass
class AudioConsentScript:
    locale: str
    consent_script: str
    reference_script: str
    min_seconds: int = 4
    max_seconds: int = 15
    chirp_clone_supported: bool = True


@dataclass
class ClonedVoice:
    voice_id: str
    locale: str
    provider: str
    consent_script: Optional[str] = None
    name: Optional[str] = None
    category: Optional[str] = None
    min_seconds: Optional[int] = None
    max_seconds: Optional[int] = None


@dataclass
class AudioSynthesizeMetadata:
    cost: int
    billed_seconds: int
    credits_per_second: int
    audio_cost: int
    text_cost: int
    duration_ms: int
    source_duration_ms: int
    speaking_rate: float
    duration_match: str
    provider: str
    voice_id: str
    mixed_with_bed: bool = False
    bed_mode: Optional[str] = None


@dataclass
class AudioSynthesis:
    audio_base64: str
    mime_type: str
    metadata: AudioSynthesizeMetadata
    video_base64: Optional[str] = None
    video_mime_type: Optional[str] = None
    voice_audio_base64: Optional[str] = None
    voice_video_base64: Optional[str] = None
    bed_audio_base64: Optional[str] = None


@dataclass
class RemuxedVideo:
    video_base64: str
    video_mime_type: str = "video/mp4"


@dataclass
class SubtitleCue:
    id: str
    text: str
    start_ms: int
    end_ms: int
    begin: str = ""
    end: str = ""


@dataclass
class SubtitleParse:
    duration_ms: int
    cues: List[SubtitleCue]


@dataclass
class SubtitlePlaygroundCue:
    original: str
    translated: str
    start_ms: int
    end_ms: int
    begin: Optional[str] = None
    end: Optional[str] = None


@dataclass
class SubtitlePlaygroundLanguage:
    language_code: str
    language: str
    srt_utf8: str
    cues: List[SubtitlePlaygroundCue]


@dataclass
class SubtitlePlayground:
    duration_ms: int
    filename: str
    source_cues: List[Dict[str, Any]]
    languages: List[SubtitlePlaygroundLanguage]
    video_id: Optional[str] = None


def _parse_transcript(data: Dict[str, Any]) -> AudioTranscript:
    segments = [
        AudioSegment(
            id=str(s.get("id", "")),
            text=s.get("text", ""),
            start_ms=int(s.get("start_ms") or 0),
            end_ms=int(s.get("end_ms") or 0),
        )
        for s in data.get("segments", [])
    ]
    return AudioTranscript(
        transcript=data.get("transcript", ""),
        duration_ms=int(data.get("duration_ms") or 0),
        segments=segments,
        provider=data.get("provider", ""),
        estimated_credit_cost=int(data.get("estimated_credit_cost") or 0),
        billed_seconds=int(data.get("billed_seconds") or 0),
        detected_language=data.get("detected_language"),
        stem_id=data.get("stem_id"),
        bed_mode=data.get("bed_mode"),
        video_id=data.get("video_id"),
        source_voice_audio_base64=data.get("source_voice_audio_base64"),
    )


def _parse_voices(data: Dict[str, Any]) -> AudioVoices:
    voices = [
        AudioVoice(
            id=v.get("id", ""),
            name=v.get("name", ""),
            gender=v.get("gender", ""),
            locale=v.get("locale", ""),
            accent_label=v.get("accent_label", ""),
            provider=v.get("provider", ""),
            category=v.get("category", "preset"),
        )
        for v in data.get("voices", [])
    ]
    return AudioVoices(voices=voices, provider=data.get("provider", ""))


def _parse_preview(data: Dict[str, Any]) -> AudioPreview:
    return AudioPreview(
        audio_base64=data.get("audio_base64", ""),
        mime_type=data.get("mime_type", "audio/wav"),
        duration_ms=int(data.get("duration_ms") or 0),
        provider=data.get("provider", ""),
        voice_id=data.get("voice_id", ""),
    )


def _parse_consent(data: Dict[str, Any]) -> AudioConsentScript:
    return AudioConsentScript(
        locale=data.get("locale", ""),
        consent_script=data.get("consent_script", ""),
        reference_script=data.get("reference_script", ""),
        min_seconds=int(data.get("min_seconds") or 4),
        max_seconds=int(data.get("max_seconds") or 15),
        chirp_clone_supported=bool(data.get("chirp_clone_supported", True)),
    )


def _parse_cloned(data: Dict[str, Any]) -> ClonedVoice:
    return ClonedVoice(
        voice_id=data.get("voice_id", ""),
        locale=data.get("locale", ""),
        provider=data.get("provider", ""),
        consent_script=data.get("consent_script"),
        name=data.get("name"),
        category=data.get("category"),
        min_seconds=data.get("min_seconds"),
        max_seconds=data.get("max_seconds"),
    )


def _parse_synthesis(data: Dict[str, Any]) -> AudioSynthesis:
    meta = data.get("metadata") or {}
    return AudioSynthesis(
        audio_base64=data.get("audio_base64", ""),
        mime_type=data.get("mime_type", "audio/wav"),
        metadata=AudioSynthesizeMetadata(
            cost=int(meta.get("cost") or 0),
            billed_seconds=int(meta.get("billed_seconds") or 0),
            credits_per_second=int(meta.get("credits_per_second") or 0),
            audio_cost=int(meta.get("audio_cost") or 0),
            text_cost=int(meta.get("text_cost") or 0),
            duration_ms=int(meta.get("duration_ms") or 0),
            source_duration_ms=int(meta.get("source_duration_ms") or 0),
            speaking_rate=float(meta.get("speaking_rate") or 0),
            duration_match=meta.get("duration_match", ""),
            provider=meta.get("provider", ""),
            voice_id=meta.get("voice_id", ""),
            mixed_with_bed=bool(meta.get("mixed_with_bed", False)),
            bed_mode=meta.get("bed_mode"),
        ),
        video_base64=data.get("video_base64"),
        video_mime_type=data.get("video_mime_type"),
        voice_audio_base64=data.get("voice_audio_base64"),
        voice_video_base64=data.get("voice_video_base64"),
        bed_audio_base64=data.get("bed_audio_base64"),
    )


def _parse_subtitle(data: Dict[str, Any]) -> SubtitleParse:
    cues = [
        SubtitleCue(
            id=str(c.get("id", "")),
            text=c.get("text", ""),
            start_ms=int(c.get("start_ms") or 0),
            end_ms=int(c.get("end_ms") or 0),
            begin=c.get("begin", ""),
            end=c.get("end", ""),
        )
        for c in data.get("cues", [])
    ]
    return SubtitleParse(duration_ms=int(data.get("duration_ms") or 0), cues=cues)


def _parse_playground(data: Dict[str, Any]) -> SubtitlePlayground:
    languages = []
    for lang in data.get("languages", []):
        cues = [
            SubtitlePlaygroundCue(
                original=c.get("original", ""),
                translated=c.get("translated", ""),
                start_ms=int(c.get("start_ms") or 0),
                end_ms=int(c.get("end_ms") or 0),
                begin=c.get("begin"),
                end=c.get("end"),
            )
            for c in lang.get("cues", [])
        ]
        languages.append(
            SubtitlePlaygroundLanguage(
                language_code=lang.get("language_code", ""),
                language=lang.get("language", ""),
                srt_utf8=lang.get("srt_utf8", ""),
                cues=cues,
            )
        )
    return SubtitlePlayground(
        duration_ms=int(data.get("duration_ms") or 0),
        filename=data.get("filename", ""),
        source_cues=list(data.get("source_cues") or []),
        languages=languages,
        video_id=data.get("video_id"),
    )


def _bool_form(value: bool) -> str:
    return "true" if value else "false"


class MediaSyncMixin:
    if TYPE_CHECKING:
        def _request(
            self,
            method: str,
            path: str,
            *,
            json: Optional[Dict[str, Any]] = None,
            params: Optional[Dict[str, Any]] = None,
            data: Optional[Dict[str, Any]] = None,
            files: Optional[Any] = None,
            timeout: Optional[float] = None,
        ) -> Dict[str, Any]: ...

    def transcribe_audio(
        self,
        file: FileInput,
        *,
        source_language_code: Optional[str] = None,
        keep_background_music: bool = False,
    ) -> AudioTranscript:
        """Speech-to-text for audio or video. Unbilled draft; billed on synthesize."""
        fn, fb, ct = _prep(file, default_name="audio.wav")
        form: Dict[str, Any] = {
            "keep_background_music": _bool_form(keep_background_music),
        }
        if source_language_code:
            form["source_language_code"] = source_language_code
        data = self._request(
            "POST", "/audio/transcribe",
            files={"file": (fn, fb, ct)}, data=form, timeout=MEDIA_TIMEOUT,
        )
        return _parse_transcript(data)

    def parse_audio_script(self, file: FileInput) -> AudioTranscript:
        """Parse a .txt/.docx/.pdf/.srt/.itt script instead of running STT."""
        fn, fb, ct = _prep(file, default_name="script.txt")
        data = self._request(
            "POST", "/audio/script",
            files={"file": (fn, fb, ct)}, timeout=MEDIA_TIMEOUT,
        )
        return _parse_transcript(data)

    def register_video(self, file: FileInput) -> str:
        """Store a source video for later muxing. Returns ``video_id``."""
        fn, fb, ct = _prep(file, default_name="video.mp4")
        data = self._request(
            "POST", "/audio/video/register",
            files={"file": (fn, fb, ct)}, timeout=MEDIA_TIMEOUT,
        )
        return str(data.get("video_id", ""))

    def list_voices(self, *, language_code: Optional[str] = None) -> AudioVoices:
        params = {"language_code": language_code} if language_code else None
        return _parse_voices(self._request("GET", "/audio/voices", params=params))

    def preview_voice(
        self,
        voice_id: str,
        *,
        language_code: Optional[str] = None,
        text: Optional[str] = None,
    ) -> AudioPreview:
        body: Dict[str, Any] = {"voice_id": voice_id}
        if language_code:
            body["language_code"] = language_code
        if text:
            body["text"] = text
        return _parse_preview(self._request("POST", "/audio/voices/preview", json=body))

    def get_voice_consent_script(
        self, *, language_code: Optional[str] = None,
    ) -> AudioConsentScript:
        params = {"language_code": language_code} if language_code else None
        return _parse_consent(
            self._request("GET", "/audio/voices/consent-script", params=params)
        )

    def clone_voice(
        self,
        reference: FileInput,
        consent: FileInput,
        *,
        language_code: Optional[str] = None,
    ) -> ClonedVoice:
        rfn, rfb, rct = _prep(reference, default_name="reference.wav")
        cfn, cfb, cct = _prep(consent, default_name="consent.wav")
        form: Dict[str, Any] = {}
        if language_code:
            form["language_code"] = language_code
        data = self._request(
            "POST", "/audio/voices/clone",
            files={
                "reference": (rfn, rfb, rct),
                "consent": (cfn, cfb, cct),
            },
            data=form or None,
            timeout=MEDIA_TIMEOUT,
        )
        return _parse_cloned(data)

    def create_byo_voice(
        self,
        reference: FileInput,
        *,
        consent: Optional[FileInput] = None,
        name: Optional[str] = None,
        language_code: Optional[str] = None,
        confirm_ownership: bool = False,
        clip_reference: bool = False,
    ) -> ClonedVoice:
        rfn, rfb, rct = _prep(reference, default_name="sample.wav")
        files: Dict[str, Any] = {"reference": (rfn, rfb, rct)}
        if consent is not None:
            cfn, cfb, cct = _prep(consent, default_name="consent.wav")
            files["consent"] = (cfn, cfb, cct)
        form: Dict[str, Any] = {
            "confirm_ownership": _bool_form(confirm_ownership),
            "clip_reference": _bool_form(clip_reference),
        }
        if name:
            form["name"] = name
        if language_code:
            form["language_code"] = language_code
        data = self._request(
            "POST", "/audio/voices/byo",
            files=files, data=form, timeout=MEDIA_TIMEOUT,
        )
        return _parse_cloned(data)

    def delete_saved_voice(self, voice_id: str) -> Dict[str, Any]:
        return self._request(
            "DELETE", "/audio/voices/saved", params={"voice_id": voice_id},
        )

    def synthesize_audio(
        self,
        *,
        language: str,
        language_code: str,
        voice_id: str,
        segments: Sequence[Dict[str, Any]],
        keep_same_length: bool = False,
        keep_background_music: bool = False,
        stem_id: Optional[str] = None,
        source_duration_ms: int = 0,
        source_transcript: Optional[str] = None,
        video_id: Optional[str] = None,
        tool: str = "api",
    ) -> AudioSynthesis:
        """Generate localized TTS (billed). Pass ``video_id`` to mux a dubbed MP4."""
        body: Dict[str, Any] = {
            "language": language,
            "language_code": language_code,
            "voice_id": voice_id,
            "segments": list(segments),
            "keep_same_length": keep_same_length,
            "keep_background_music": keep_background_music,
            "source_duration_ms": source_duration_ms,
            "tool": tool,
        }
        if stem_id:
            body["stem_id"] = stem_id
        if source_transcript:
            body["source_transcript"] = source_transcript
        if video_id:
            body["video_id"] = video_id
        data = self._request(
            "POST", "/audio/synthesize", json=body, timeout=MEDIA_TIMEOUT,
        )
        return _parse_synthesis(data)

    def remux_video(self, video_id: str, audio_base64: str) -> RemuxedVideo:
        data = self._request(
            "POST", "/audio/remux-video",
            json={"video_id": video_id, "audio_base64": audio_base64},
            timeout=MEDIA_TIMEOUT,
        )
        return RemuxedVideo(
            video_base64=data.get("video_base64", ""),
            video_mime_type=data.get("video_mime_type", "video/mp4"),
        )

    def parse_subtitle(self, file: FileInput) -> SubtitleParse:
        fn, fb, ct = _prep(file, default_name="subtitles.srt")
        data = self._request(
            "POST", "/subtitle/parse",
            files={"file": (fn, fb, ct)}, timeout=MEDIA_TIMEOUT,
        )
        return _parse_subtitle(data)

    def localize_subtitles(
        self,
        target_language_codes: Sequence[str],
        *,
        subtitle: Optional[FileInput] = None,
        video: Optional[FileInput] = None,
        glossary: Optional[FileInput] = None,
        source_language_code: str = "en",
        context: str = "",
        formality: Optional[str] = None,
        campaign_ids: Optional[Sequence[int]] = None,
    ) -> SubtitlePlayground:
        """In-memory SRT localize. Provide ``subtitle`` and/or ``video`` (STT)."""
        import json

        files: Dict[str, Any] = {}
        if subtitle is not None:
            fn, fb, ct = _prep(subtitle, default_name="subtitles.srt")
            files["subtitle"] = (fn, fb, ct)
        if video is not None:
            fn, fb, ct = _prep(video, default_name="video.mp4")
            files["video"] = (fn, fb, ct)
        if glossary is not None:
            fn, fb, ct = _prep(glossary, default_name="glossary.csv")
            files["glossary"] = (fn, fb, ct)
        form: Dict[str, Any] = {
            "target_language_codes": json.dumps(list(target_language_codes)),
            "source_language_code": source_language_code,
            "context": context,
        }
        if formality:
            form["formality"] = formality
        if campaign_ids:
            form["campaign_ids"] = json.dumps(list(campaign_ids))
        data = self._request(
            "POST", "/subtitle/playground",
            files=files or None, data=form, timeout=MEDIA_TIMEOUT,
        )
        return _parse_playground(data)

    def upload_subtitle(
        self,
        file: FileInput,
        *,
        auto_localize: bool = False,
        target_languages: Optional[Sequence[str]] = None,
        context: Optional[str] = None,
        glossary: Optional[str] = None,
        source_language: Optional[str] = None,
    ) -> Dict[str, Any]:
        fn, fb, ct = _prep(file, default_name="subtitles.srt")
        params: Dict[str, Any] = {"auto_localize": auto_localize}
        if target_languages:
            params["target_languages"] = list(target_languages)
        if context:
            params["context"] = context
        if glossary:
            params["glossary"] = glossary
        if source_language:
            params["source_language"] = source_language
        return self._request(
            "POST", "/subtitle/upload",
            files={"file": (fn, fb, ct)}, params=params, timeout=MEDIA_TIMEOUT,
        )

    def list_subtitles(self) -> Dict[str, Any]:
        return self._request("GET", "/subtitle/list")

    def localize_subtitle_file(
        self,
        file_path: str,
        target_languages: Sequence[str],
        *,
        context: Optional[str] = None,
        glossary: Optional[str] = None,
    ) -> Dict[str, Any]:
        body: Dict[str, Any] = {
            "file_path": file_path,
            "target_languages": list(target_languages),
        }
        if context:
            body["context"] = context
        if glossary:
            body["glossary"] = glossary
        return self._request("POST", "/subtitle/localize", json=body, timeout=MEDIA_TIMEOUT)

    def get_subtitle_download_url(self, file_path: str) -> str:
        data = self._request(
            "GET", "/subtitle/download-url", params={"file_path": file_path},
        )
        return str(data.get("download_url", ""))

    def delete_subtitle(self, file_path: str) -> Dict[str, Any]:
        return self._request("DELETE", "/subtitle/delete", params={"file_path": file_path})


class MediaAsyncMixin:
    if TYPE_CHECKING:
        async def _request(
            self,
            method: str,
            path: str,
            *,
            json: Optional[Dict[str, Any]] = None,
            params: Optional[Dict[str, Any]] = None,
            data: Optional[Dict[str, Any]] = None,
            files: Optional[Any] = None,
            timeout: Optional[float] = None,
        ) -> Dict[str, Any]: ...

    async def transcribe_audio(
        self,
        file: FileInput,
        *,
        source_language_code: Optional[str] = None,
        keep_background_music: bool = False,
    ) -> AudioTranscript:
        fn, fb, ct = _prep(file, default_name="audio.wav")
        form: Dict[str, Any] = {
            "keep_background_music": _bool_form(keep_background_music),
        }
        if source_language_code:
            form["source_language_code"] = source_language_code
        data = await self._request(
            "POST", "/audio/transcribe",
            files={"file": (fn, fb, ct)}, data=form, timeout=MEDIA_TIMEOUT,
        )
        return _parse_transcript(data)

    async def parse_audio_script(self, file: FileInput) -> AudioTranscript:
        fn, fb, ct = _prep(file, default_name="script.txt")
        data = await self._request(
            "POST", "/audio/script",
            files={"file": (fn, fb, ct)}, timeout=MEDIA_TIMEOUT,
        )
        return _parse_transcript(data)

    async def register_video(self, file: FileInput) -> str:
        fn, fb, ct = _prep(file, default_name="video.mp4")
        data = await self._request(
            "POST", "/audio/video/register",
            files={"file": (fn, fb, ct)}, timeout=MEDIA_TIMEOUT,
        )
        return str(data.get("video_id", ""))

    async def list_voices(self, *, language_code: Optional[str] = None) -> AudioVoices:
        params = {"language_code": language_code} if language_code else None
        return _parse_voices(await self._request("GET", "/audio/voices", params=params))

    async def preview_voice(
        self,
        voice_id: str,
        *,
        language_code: Optional[str] = None,
        text: Optional[str] = None,
    ) -> AudioPreview:
        body: Dict[str, Any] = {"voice_id": voice_id}
        if language_code:
            body["language_code"] = language_code
        if text:
            body["text"] = text
        return _parse_preview(
            await self._request("POST", "/audio/voices/preview", json=body)
        )

    async def get_voice_consent_script(
        self, *, language_code: Optional[str] = None,
    ) -> AudioConsentScript:
        params = {"language_code": language_code} if language_code else None
        return _parse_consent(
            await self._request("GET", "/audio/voices/consent-script", params=params)
        )

    async def clone_voice(
        self,
        reference: FileInput,
        consent: FileInput,
        *,
        language_code: Optional[str] = None,
    ) -> ClonedVoice:
        rfn, rfb, rct = _prep(reference, default_name="reference.wav")
        cfn, cfb, cct = _prep(consent, default_name="consent.wav")
        form: Dict[str, Any] = {}
        if language_code:
            form["language_code"] = language_code
        data = await self._request(
            "POST", "/audio/voices/clone",
            files={
                "reference": (rfn, rfb, rct),
                "consent": (cfn, cfb, cct),
            },
            data=form or None,
            timeout=MEDIA_TIMEOUT,
        )
        return _parse_cloned(data)

    async def create_byo_voice(
        self,
        reference: FileInput,
        *,
        consent: Optional[FileInput] = None,
        name: Optional[str] = None,
        language_code: Optional[str] = None,
        confirm_ownership: bool = False,
        clip_reference: bool = False,
    ) -> ClonedVoice:
        rfn, rfb, rct = _prep(reference, default_name="sample.wav")
        files: Dict[str, Any] = {"reference": (rfn, rfb, rct)}
        if consent is not None:
            cfn, cfb, cct = _prep(consent, default_name="consent.wav")
            files["consent"] = (cfn, cfb, cct)
        form: Dict[str, Any] = {
            "confirm_ownership": _bool_form(confirm_ownership),
            "clip_reference": _bool_form(clip_reference),
        }
        if name:
            form["name"] = name
        if language_code:
            form["language_code"] = language_code
        data = await self._request(
            "POST", "/audio/voices/byo",
            files=files, data=form, timeout=MEDIA_TIMEOUT,
        )
        return _parse_cloned(data)

    async def delete_saved_voice(self, voice_id: str) -> Dict[str, Any]:
        return await self._request(
            "DELETE", "/audio/voices/saved", params={"voice_id": voice_id},
        )

    async def synthesize_audio(
        self,
        *,
        language: str,
        language_code: str,
        voice_id: str,
        segments: Sequence[Dict[str, Any]],
        keep_same_length: bool = False,
        keep_background_music: bool = False,
        stem_id: Optional[str] = None,
        source_duration_ms: int = 0,
        source_transcript: Optional[str] = None,
        video_id: Optional[str] = None,
        tool: str = "api",
    ) -> AudioSynthesis:
        body: Dict[str, Any] = {
            "language": language,
            "language_code": language_code,
            "voice_id": voice_id,
            "segments": list(segments),
            "keep_same_length": keep_same_length,
            "keep_background_music": keep_background_music,
            "source_duration_ms": source_duration_ms,
            "tool": tool,
        }
        if stem_id:
            body["stem_id"] = stem_id
        if source_transcript:
            body["source_transcript"] = source_transcript
        if video_id:
            body["video_id"] = video_id
        data = await self._request(
            "POST", "/audio/synthesize", json=body, timeout=MEDIA_TIMEOUT,
        )
        return _parse_synthesis(data)

    async def remux_video(self, video_id: str, audio_base64: str) -> RemuxedVideo:
        data = await self._request(
            "POST", "/audio/remux-video",
            json={"video_id": video_id, "audio_base64": audio_base64},
            timeout=MEDIA_TIMEOUT,
        )
        return RemuxedVideo(
            video_base64=data.get("video_base64", ""),
            video_mime_type=data.get("video_mime_type", "video/mp4"),
        )

    async def parse_subtitle(self, file: FileInput) -> SubtitleParse:
        fn, fb, ct = _prep(file, default_name="subtitles.srt")
        data = await self._request(
            "POST", "/subtitle/parse",
            files={"file": (fn, fb, ct)}, timeout=MEDIA_TIMEOUT,
        )
        return _parse_subtitle(data)

    async def localize_subtitles(
        self,
        target_language_codes: Sequence[str],
        *,
        subtitle: Optional[FileInput] = None,
        video: Optional[FileInput] = None,
        glossary: Optional[FileInput] = None,
        source_language_code: str = "en",
        context: str = "",
        formality: Optional[str] = None,
        campaign_ids: Optional[Sequence[int]] = None,
    ) -> SubtitlePlayground:
        import json

        files: Dict[str, Any] = {}
        if subtitle is not None:
            fn, fb, ct = _prep(subtitle, default_name="subtitles.srt")
            files["subtitle"] = (fn, fb, ct)
        if video is not None:
            fn, fb, ct = _prep(video, default_name="video.mp4")
            files["video"] = (fn, fb, ct)
        if glossary is not None:
            fn, fb, ct = _prep(glossary, default_name="glossary.csv")
            files["glossary"] = (fn, fb, ct)
        form: Dict[str, Any] = {
            "target_language_codes": json.dumps(list(target_language_codes)),
            "source_language_code": source_language_code,
            "context": context,
        }
        if formality:
            form["formality"] = formality
        if campaign_ids:
            form["campaign_ids"] = json.dumps(list(campaign_ids))
        data = await self._request(
            "POST", "/subtitle/playground",
            files=files or None, data=form, timeout=MEDIA_TIMEOUT,
        )
        return _parse_playground(data)

    async def upload_subtitle(
        self,
        file: FileInput,
        *,
        auto_localize: bool = False,
        target_languages: Optional[Sequence[str]] = None,
        context: Optional[str] = None,
        glossary: Optional[str] = None,
        source_language: Optional[str] = None,
    ) -> Dict[str, Any]:
        fn, fb, ct = _prep(file, default_name="subtitles.srt")
        params: Dict[str, Any] = {"auto_localize": auto_localize}
        if target_languages:
            params["target_languages"] = list(target_languages)
        if context:
            params["context"] = context
        if glossary:
            params["glossary"] = glossary
        if source_language:
            params["source_language"] = source_language
        return await self._request(
            "POST", "/subtitle/upload",
            files={"file": (fn, fb, ct)}, params=params, timeout=MEDIA_TIMEOUT,
        )

    async def list_subtitles(self) -> Dict[str, Any]:
        return await self._request("GET", "/subtitle/list")

    async def localize_subtitle_file(
        self,
        file_path: str,
        target_languages: Sequence[str],
        *,
        context: Optional[str] = None,
        glossary: Optional[str] = None,
    ) -> Dict[str, Any]:
        body: Dict[str, Any] = {
            "file_path": file_path,
            "target_languages": list(target_languages),
        }
        if context:
            body["context"] = context
        if glossary:
            body["glossary"] = glossary
        return await self._request(
            "POST", "/subtitle/localize", json=body, timeout=MEDIA_TIMEOUT,
        )

    async def get_subtitle_download_url(self, file_path: str) -> str:
        data = await self._request(
            "GET", "/subtitle/download-url", params={"file_path": file_path},
        )
        return str(data.get("download_url", ""))

    async def delete_subtitle(self, file_path: str) -> Dict[str, Any]:
        return await self._request(
            "DELETE", "/subtitle/delete", params={"file_path": file_path},
        )
