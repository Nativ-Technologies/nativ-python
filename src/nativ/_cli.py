"""Nativ CLI -- translate and manage localization from your terminal.

Usage::

    nativ translate "Hello world" --to French
    nativ batch "Sign up" "Log in" --to German
    nativ languages
    nativ tm search "hello" --target-lang fr
    nativ tm stats
    echo "Hello" | nativ translate --to French
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict
from typing import List, Optional, Sequence

from ._version import __version__


def _get_client():
    from . import Nativ
    return Nativ()


def _json_out(obj) -> str:
    if hasattr(obj, "__dataclass_fields__"):
        obj = asdict(obj)
    return json.dumps(obj, indent=2, ensure_ascii=False)


def _read_stdin_texts() -> Optional[List[str]]:
    if not sys.stdin.isatty():
        text = sys.stdin.read().strip()
        if text:
            return [text]
    return None


# ---------------------------------------------------------------------------
# Commands
# ---------------------------------------------------------------------------


def cmd_translate(args: argparse.Namespace) -> int:
    text = args.text
    if text is None or text == "-":
        stdin = _read_stdin_texts()
        if not stdin:
            print("Error: provide text as argument or pipe via stdin", file=sys.stderr)
            return 1
        text = stdin[0]

    client = _get_client()
    try:
        result = client.translate(
            text,
            target_language=args.to,
            target_language_code=args.to_code,
            source_language=args.source or "English",
            source_language_code=args.source_code or "en",
            context=args.context,
            glossary=args.glossary,
            formality=args.formality,
            max_characters=args.max_chars,
            backtranslate=args.backtranslate,
        )
    finally:
        client.close()

    if args.json:
        print(_json_out(result))
    else:
        print(result.translated_text)
        if result.backtranslation:
            print(f"\nBack-translation: {result.backtranslation}")
        if result.rationale:
            print(f"\nRationale: {result.rationale}")
        if result.tm_match and result.tm_match.score > 0:
            print(f"\nTM match: {result.tm_match.score:.0f}% ({result.tm_match.match_type})")
    return 0


def cmd_batch(args: argparse.Namespace) -> int:
    texts = list(args.texts)
    if not texts:
        stdin = _read_stdin_texts()
        if stdin:
            texts = stdin[0].splitlines()
    if not texts:
        print("Error: provide texts as arguments or pipe via stdin (one per line)", file=sys.stderr)
        return 1

    client = _get_client()
    try:
        results = client.translate_batch(
            texts,
            target_language=args.to,
            target_language_code=args.to_code,
            source_language=args.source or "English",
            source_language_code=args.source_code or "en",
            context=args.context,
            formality=args.formality,
        )
    finally:
        client.close()

    if args.json:
        print(json.dumps([asdict(r) for r in results], indent=2, ensure_ascii=False))
    else:
        for orig, result in zip(texts, results):
            print(f"{orig}  ->  {result.translated_text}")
    return 0


def cmd_languages(args: argparse.Namespace) -> int:
    client = _get_client()
    try:
        langs = client.get_languages()
    finally:
        client.close()

    if args.json:
        print(json.dumps([asdict(lang) for lang in langs], indent=2, ensure_ascii=False))
    else:
        for lang in langs:
            parts = [f"{lang.language} ({lang.language_code})"]
            if lang.formality:
                parts.append(f"formality={lang.formality}")
            print("  ".join(parts))
    return 0


def cmd_tm_search(args: argparse.Namespace) -> int:
    client = _get_client()
    try:
        matches = client.search_tm(
            args.query,
            source_language_code=args.source_lang or "en",
            target_language_code=args.target_lang,
            min_score=args.min_score,
            limit=args.limit,
        )
    finally:
        client.close()

    if args.json:
        print(json.dumps([asdict(m) for m in matches], indent=2, ensure_ascii=False))
    else:
        if not matches:
            print("No matches found.")
        for m in matches:
            print(f"  {m.score:.0f}%  {m.source_text}  ->  {m.target_text}")
    return 0


def cmd_tm_list(args: argparse.Namespace) -> int:
    client = _get_client()
    try:
        result = client.list_tm_entries(
            source_language_code=args.source_lang,
            target_language_code=args.target_lang,
            search=args.search,
            enabled_only=args.enabled_only,
            limit=args.limit,
            offset=args.offset,
        )
    finally:
        client.close()

    if args.json:
        print(_json_out(result))
    else:
        print(f"Showing {len(result.entries)} of {result.total} entries\n")
        for e in result.entries:
            status = "on " if e.enabled else "off"
            print(f"  [{status}] {e.id[:8]}  {e.source_text}  ->  {e.target_text}  ({e.source_language_code}->{e.target_language_code})")
    return 0


def cmd_tm_add(args: argparse.Namespace) -> int:
    client = _get_client()
    try:
        entry = client.add_tm_entry(
            args.source,
            args.target,
            args.source_lang,
            args.target_lang,
            name=args.name,
        )
    finally:
        client.close()

    if args.json:
        print(_json_out(entry))
    else:
        print(f"Added: {entry.id}  {entry.source_text}  ->  {entry.target_text}")
    return 0


def cmd_tm_delete(args: argparse.Namespace) -> int:
    client = _get_client()
    try:
        ok = client.delete_tm_entry(args.id)
    finally:
        client.close()

    if ok:
        print(f"Deleted {args.id}")
    else:
        print(f"Failed to delete {args.id}", file=sys.stderr)
        return 1
    return 0


def cmd_tm_stats(args: argparse.Namespace) -> int:
    client = _get_client()
    try:
        stats = client.get_tm_stats()
    finally:
        client.close()

    if args.json:
        print(_json_out(stats))
    else:
        print(f"Total:    {stats.total}")
        print(f"Enabled:  {stats.enabled}")
        print(f"Disabled: {stats.disabled}")
        if stats.by_source:
            print("\nBy source:")
            for src, counts in stats.by_source.items():
                print(f"  {src}: {counts}")
    return 0


def cmd_style_guides(args: argparse.Namespace) -> int:
    client = _get_client()
    try:
        guides = client.get_style_guides()
    finally:
        client.close()

    if args.json:
        print(json.dumps([asdict(g) for g in guides], indent=2, ensure_ascii=False))
    else:
        if not guides:
            print("No style guides.")
        for g in guides:
            status = "enabled" if g.is_enabled else "disabled"
            print(f"  [{status}] {g.title}")
            for line in g.content.splitlines()[:3]:
                print(f"    {line}")
            if len(g.content.splitlines()) > 3:
                print("    ...")
    return 0


def cmd_brand_voice(args: argparse.Namespace) -> int:
    client = _get_client()
    try:
        bv = client.get_brand_voice()
    finally:
        client.close()

    if args.json:
        print(_json_out(bv))
    else:
        if bv.exists and bv.prompt:
            print(bv.prompt)
        else:
            print("No brand voice configured.")
    return 0


def cmd_extract(args: argparse.Namespace) -> int:
    client = _get_client()
    try:
        result = client.extract_text(args.file)
    finally:
        client.close()

    if args.json:
        print(_json_out(result))
    else:
        print(result.extracted_text)
    return 0


def cmd_inspect(args: argparse.Namespace) -> int:
    countries = args.countries.split(",") if args.countries else None
    client = _get_client()
    try:
        result = client.inspect_image(args.file, countries=countries)
    finally:
        client.close()

    if args.json:
        print(_json_out(result))
    else:
        print(f"Verdict: {result.verdict}")
        if result.affected_countries:
            print()
            for ac in result.affected_countries:
                print(f"  {ac.country}: {ac.issue}")
                print(f"    Suggestion: {ac.suggestion}")
    return 0


# ---------------------------------------------------------------------------
# Parser
# ---------------------------------------------------------------------------

def _add_output_flag(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--json", action="store_true", help="output as JSON")


def _add_lang_flags(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--to", required=True, metavar="LANG",
                        help="target language (e.g. French, German)")
    parser.add_argument("--to-code", metavar="CODE",
                        help="target language ISO code (e.g. fr)")
    parser.add_argument("--from", dest="source", metavar="LANG",
                        help="source language (default: English)")
    parser.add_argument("--from-code", dest="source_code", metavar="CODE",
                        help="source language code (default: en)")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="nativ",
        description="Nativ CLI -- AI-powered localization from your terminal",
    )
    parser.add_argument(
        "--version", action="version", version=f"nativ {__version__}"
    )
    sub = parser.add_subparsers(dest="command")

    # -- translate -------------------------------------------------------
    p = sub.add_parser("translate", aliases=["t"],
                       help="translate text")
    p.add_argument("text", nargs="?", default=None,
                   help='text to translate (or pipe via stdin, or "-")')
    _add_lang_flags(p)
    p.add_argument("--context", help="context hint for the translation")
    p.add_argument("--glossary",
                   help="inline glossary CSV (term,translation)")
    p.add_argument("--formality",
                   choices=["very_informal", "informal", "neutral",
                            "formal", "very_formal"])
    p.add_argument("--max-chars", type=int, metavar="N",
                   help="character limit")
    p.add_argument("--backtranslate", action="store_true",
                   help="include back-translation")
    _add_output_flag(p)
    p.set_defaults(func=cmd_translate)

    # -- batch -----------------------------------------------------------
    p = sub.add_parser("batch", aliases=["b"],
                       help="translate multiple texts")
    p.add_argument("texts", nargs="*",
                   help="texts to translate (or pipe via stdin, one per line)")
    _add_lang_flags(p)
    p.add_argument("--context", help="context hint")
    p.add_argument("--formality",
                   choices=["very_informal", "informal", "neutral",
                            "formal", "very_formal"])
    _add_output_flag(p)
    p.set_defaults(func=cmd_batch)

    # -- languages -------------------------------------------------------
    p = sub.add_parser("languages", aliases=["lang"],
                       help="list configured languages")
    _add_output_flag(p)
    p.set_defaults(func=cmd_languages)

    # -- tm (translation memory) -----------------------------------------
    tm = sub.add_parser("tm", help="translation memory commands")
    tm_sub = tm.add_subparsers(dest="tm_command")

    # tm search
    p = tm_sub.add_parser("search", help="fuzzy-search the translation memory")
    p.add_argument("query", help="text to search for")
    p.add_argument("--source-lang", metavar="CODE",
                   help="source language code (default: en)")
    p.add_argument("--target-lang", metavar="CODE",
                   help="filter by target language code")
    p.add_argument("--min-score", type=float, default=0, metavar="N",
                   help="minimum match score (0-100)")
    p.add_argument("--limit", type=int, default=10, help="max results")
    _add_output_flag(p)
    p.set_defaults(func=cmd_tm_search)

    # tm list
    p = tm_sub.add_parser("list", aliases=["ls"],
                          help="list translation memory entries")
    p.add_argument("--source-lang", metavar="CODE")
    p.add_argument("--target-lang", metavar="CODE")
    p.add_argument("--search", metavar="TEXT", help="filter by text")
    p.add_argument("--enabled-only", action="store_true")
    p.add_argument("--limit", type=int, default=20)
    p.add_argument("--offset", type=int, default=0)
    _add_output_flag(p)
    p.set_defaults(func=cmd_tm_list)

    # tm add
    p = tm_sub.add_parser("add", help="add a translation memory entry")
    p.add_argument("source", help="source text")
    p.add_argument("target", help="target (translated) text")
    p.add_argument("--source-lang", required=True, metavar="CODE",
                   help="source language code")
    p.add_argument("--target-lang", required=True, metavar="CODE",
                   help="target language code")
    p.add_argument("--name", help="optional label for this entry")
    _add_output_flag(p)
    p.set_defaults(func=cmd_tm_add)

    # tm delete
    p = tm_sub.add_parser("delete", aliases=["rm"],
                          help="delete a TM entry")
    p.add_argument("id", help="entry ID")
    p.set_defaults(func=cmd_tm_delete)

    # tm stats
    p = tm_sub.add_parser("stats", help="translation memory statistics")
    _add_output_flag(p)
    p.set_defaults(func=cmd_tm_stats)

    # -- style-guides ----------------------------------------------------
    p = sub.add_parser("style-guides", aliases=["sg"],
                       help="list style guides")
    _add_output_flag(p)
    p.set_defaults(func=cmd_style_guides)

    # -- brand-voice -----------------------------------------------------
    p = sub.add_parser("brand-voice", aliases=["bv"],
                       help="show brand voice prompt")
    _add_output_flag(p)
    p.set_defaults(func=cmd_brand_voice)

    # -- extract (OCR) ---------------------------------------------------
    p = sub.add_parser("extract", help="extract text from an image (OCR)")
    p.add_argument("file", help="path to image file")
    _add_output_flag(p)
    p.set_defaults(func=cmd_extract)

    # -- inspect ---------------------------------------------------------
    p = sub.add_parser("inspect",
                       help="cultural sensitivity check on an image")
    p.add_argument("file", help="path to image file")
    p.add_argument("--countries",
                   help="comma-separated country list to check")
    _add_output_flag(p)
    p.set_defaults(func=cmd_inspect)

    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if not args.command:
        parser.print_help()
        return 0

    if args.command == "tm" and not getattr(args, "tm_command", None):
        parser.parse_args(["tm", "--help"])
        return 0

    try:
        return args.func(args)
    except KeyboardInterrupt:
        print("\nInterrupted.", file=sys.stderr)
        return 130
    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1


def cli_entry() -> None:
    """Entry point for the ``nativ`` console script."""
    sys.exit(main())
