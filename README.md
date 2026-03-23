# LH-Debrief

Speaker diarization, transcription, and AI analysis for meeting recordings.

> **Status:** Under active development. Documentation and features are being built out.

## What it does

LH-Debrief takes audio or video recordings and produces speaker-labeled transcripts plus structured AI analysis — configurable for different use cases (business meetings, therapy sessions, research discussions, etc.).

```
Audio File → Speaker Diarization → Transcription → AI Analysis → Briefing
              (Pyannote 3.1)        (Whisper)      (Claude/Ollama)
```

## Quick start

```bash
# Install
uv sync

# Run
python src/diarize.py meeting.mp4 -o output/ --profile business -c "Q3 planning"
```

## Features

- **Speaker diarization** — identifies who spoke when (Pyannote 3.1)
- **Transcription** — speech-to-text with language detection and translation (Whisper)
- **Composable analysis** — modular block/profile system for different analysis lenses
- **Multiple providers** — Anthropic Claude or local models via Ollama
- **Extensible** — add new analysis blocks and profiles via TOML files, no code changes

## Documentation

<!-- TODO: Add ReadTheDocs link once deployed -->

Full documentation available at the [docs site](docs/index.md).

## Requirements

- Python 3.12+
- FFmpeg: `brew install ffmpeg`
- `.env` with `HF_TOKEN` (required) and `ANTHROPIC_API_KEY` (optional if using Ollama)

## License

<!-- TODO: Add license -->
