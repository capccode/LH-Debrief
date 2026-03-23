# LH-Debrief

Speaker diarization, transcription, and AI analysis for meeting recordings.

## What it does

LH-Debrief takes audio or video recordings and produces:

- **Speaker-labeled transcripts** — who said what, with timestamps
- **Structured analysis** — configurable via profiles and blocks
- **Formatted briefings** — markdown documents with actionable insights

## How it works

```
Audio File → Speaker Diarization → Transcription → AI Analysis → Briefing
              (Pyannote 3.1)        (Whisper)      (Claude/Ollama)
```

## Quick start

See [Getting Started](getting-started.md) for installation and first run.

## Extensibility

- **[Profiles](profiles.md)** — pre-configured analysis lenses (business, therapy, etc.)
- **[Blocks](blocks.md)** — composable analysis dimensions (add your own in TOML)
- **[Providers](providers.md)** — Anthropic Claude or local models via Ollama
