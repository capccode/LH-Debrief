# LH-Debrief

Speaker diarization, transcription, and AI analysis for recorded conversations.

## What it does

LH-Debrief takes audio or video recordings and produces:

- **Speaker-labeled transcripts** — who said what, with timestamps
- **Structured analysis** — configurable via [profiles](profiles.md) and [blocks](blocks.md)
- **Formatted briefings** — markdown documents with actionable insights

## How it works

```
Audio/Video → Speaker Diarization → Transcription → AI Analysis → Briefing
               (Pyannote 3.1)        (Whisper)     (Claude/Ollama)
```

Analysis is driven by **profiles** — TOML configurations that define which analysis dimensions (blocks) to extract and how to frame the conversation. Adding a new use case means creating a TOML file, not writing Python.

## Quick start

```bash
# Install
uv sync

# Configure (see Getting Started for details)
cp .env.example .env
# Edit .env with your tokens

# Run
python src/diarize.py meeting.mp4 -o output/ --profile business
```

See [Getting Started](getting-started.md) for full setup instructions.

## Key concepts

| Concept | What it is | Learn more |
|---------|-----------|------------|
| **Profiles** | Analysis lenses — which blocks to use and how to frame the conversation | [Profiles](profiles.md) |
| **Blocks** | Individual analysis dimensions — TOML files defining a prompt + output shape | [Blocks](blocks.md) |
| **Providers** | LLM backends — Anthropic Claude (cloud) or Ollama (local) | [Providers](providers.md) |

## Built-in profiles

| Profile | Use case |
|---------|----------|
| `business` | Corporate meetings — decisions, action items, stakeholder dynamics |
| `therapy` | Therapy sessions — emotional patterns, relational dynamics, frameworks |

## Documentation

- **[Quickstart](quickstart.md)** — CLI, API, or Desktop in 60 seconds
- **[Getting Started](getting-started.md)** — installation, configuration, first run
- **[Profiles](profiles.md)** — using and creating analysis profiles
- **[Blocks](blocks.md)** — understanding and creating analysis blocks
- **[Providers](providers.md)** — Anthropic Claude and Ollama setup
- **[CLI Reference](cli-reference.md)** — all flags and usage examples
- **[API Reference](api-reference.md)** — REST + WebSocket API for programmatic access
- **[Deployment](deployment.md)** — local dev, Tailscale, AWS, and desktop app setup
- **[Desktop App](desktop.md)** — Electron wrapper for click-to-run experience
- **[Contributing](contributing.md)** — how to add blocks, profiles, providers, or features
