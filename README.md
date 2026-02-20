# Nativ Python SDK

The official Python client for the [Nativ](https://usenativ.com) AI localization platform.

Wraps the full Nativ REST API with **sync and async** clients, typed responses, and zero config — just add your API key.

## Installation

```bash
pip install nativ
```

## Quick start

```python
from nativ import Nativ

client = Nativ(api_key="nativ_...")  # or set NATIV_API_KEY env var

# Translate text
result = client.translate("Launch your product globally", target_language="French")
print(result.translated_text)  # "Lancez votre produit à l'international"
print(result.tm_match)         # TM match details (score, source, etc.)

# Batch translate
results = client.translate_batch(
    ["Sign up", "Log in", "Settings"],
    target_language="German",
)
for r in results:
    print(r.translated_text)
```

## CLI

The `nativ` command is included when you install the SDK. Set your API key once and use it from any terminal or CI pipeline.

```bash
export NATIV_API_KEY="nativ_..."
```

### Translate

```bash
nativ translate "Launch your product globally" --to French
# Lancez votre produit à l'international

nativ t "Hello" --to German --formality formal --backtranslate --json
```

### Batch translate

```bash
nativ batch "Sign up" "Log in" "Settings" --to Spanish

# Or pipe from stdin (one text per line):
cat strings.txt | nativ batch --to Japanese
```

### Translation memory

```bash
nativ tm search "Hello" --target-lang fr
nativ tm list --target-lang fr --limit 10
nativ tm add "Hello" "Bonjour" --source-lang en --target-lang fr
nativ tm stats
nativ tm delete <entry-id>
```

### Languages, style guides, brand voice

```bash
nativ languages
nativ style-guides
nativ brand-voice
```

### OCR & image inspection

```bash
nativ extract screenshot.png
nativ inspect ad_creative.jpg --countries "Japan,Brazil"
```

### JSON output

Every command supports `--json` for machine-readable output, perfect for shell scripts and CI:

```bash
nativ translate "Hello" --to French --json | jq .translated_text
```

## Async usage

```python
import asyncio
from nativ import AsyncNativ

async def main():
    async with AsyncNativ() as client:
        result = await client.translate("Hello", target_language="Japanese")
        print(result.translated_text)

asyncio.run(main())
```

## Features

### Translation

```python
result = client.translate(
    "Welcome to our platform",
    target_language="Spanish",
    context="SaaS onboarding email subject line",
    formality="formal",
    backtranslate=True,
)

print(result.translated_text)   # translated text
print(result.backtranslation)   # back-translation for QA
print(result.rationale)         # AI explanation of translation choices
print(result.tm_match.score)    # TM match percentage
```

### OCR — extract text from images

```python
result = client.extract_text("screenshot.png")
print(result.extracted_text)
```

### Image culturalization

```python
result = client.culturalize_image(
    "banner_en.png",
    text="Soldes d'été",
    language_code="fr",
    num_images=3,
)
for img in result.images:
    # img.image_base64 contains the generated image
    pass
```

### Cultural sensitivity inspection

```python
result = client.inspect_image("ad_creative.jpg")
print(result.verdict)  # "SAFE" or "NOT SAFE"
for issue in result.affected_countries:
    print(f"{issue.country}: {issue.issue} → {issue.suggestion}")
```

### Translation memory

```python
# Search
matches = client.search_tm("Sign up", target_language_code="fr")
for m in matches:
    print(f"{m.score:.0f}% — {m.source_text} → {m.target_text}")

# Add entry
client.add_tm_entry(
    source_text="Sign up",
    target_text="S'inscrire",
    source_language_code="en",
    target_language_code="fr-FR",
    name="onboarding CTA",
)

# List & filter
entries = client.list_tm_entries(target_language_code="fr-FR", enabled_only=True)
print(f"{entries.total} entries")

# Stats
stats = client.get_tm_stats()
print(f"{stats.total} total, {stats.enabled} enabled")
```

### Languages

```python
languages = client.get_languages()
for lang in languages:
    print(f"{lang.language} ({lang.language_code}) — formality: {lang.formality}")
```

### Style guides & brand voice

```python
# List style guides
guides = client.get_style_guides()
for g in guides:
    print(f"{g.title} — {'enabled' if g.is_enabled else 'disabled'}")

# Get brand voice prompt
voice = client.get_brand_voice()
print(voice.prompt)

# Create a style guide
client.create_style_guide(
    title="Tone of Voice",
    content="Always use active voice. Avoid jargon.",
)
```

## Error handling

```python
from nativ import Nativ, InsufficientCreditsError, AuthenticationError

client = Nativ()

try:
    result = client.translate("Hello", target_language="French")
except AuthenticationError:
    print("Bad API key")
except InsufficientCreditsError:
    print("Top up at dashboard.usenativ.com")
```

All exceptions inherit from `NativError` and carry `status_code` and `body` attributes.

| Exception                  | HTTP | When                          |
|----------------------------|------|-------------------------------|
| `AuthenticationError`      | 401  | Invalid or missing API key    |
| `InsufficientCreditsError` | 402  | Not enough credits            |
| `ValidationError`          | 400  | Bad request parameters        |
| `NotFoundError`            | 404  | Resource not found            |
| `RateLimitError`           | 429  | Too many requests             |
| `ServerError`              | 5xx  | Nativ API server error        |

## Configuration

```python
client = Nativ(
    api_key="nativ_...",          # or NATIV_API_KEY env var
    base_url="https://...",       # or NATIV_API_URL env var (default: api.usenativ.com)
    timeout=120.0,                # request timeout in seconds
)
```

## Building on top of this SDK

This SDK is the foundation for Nativ integrations:

- **CLI** — `nativ translate "Hello" --to French` (included, see above)
- **[nativ-mcp](https://pypi.org/project/nativ-mcp/)** — MCP server for Claude, Cursor, etc.
- **[langchain-nativ](https://pypi.org/project/langchain-nativ/)** — LangChain tool for AI agents
- **CrewAI** — works via langchain-nativ (see [CrewAI docs](https://github.com/Nativ-Technologies/nativ-python))

## License

MIT
