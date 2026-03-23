# CLI Reference

## Usage

```bash
python src/diarize.py <audio> [options]
python src/diarize.py --list-profiles
python src/diarize.py --list-blocks
```

The `audio` argument is required for all commands except `--list-profiles` and `--list-blocks`.

## Arguments

| Argument | Description |
|----------|-------------|
| `audio` | Path to audio or video file (wav, mp3, m4a, mp4, etc.) |

## Options

### Output

| Flag | Description |
|------|-------------|
| `-o, --output PATH` | Output directory (creates a subfolder per recording) |

### Audio processing

| Flag | Description |
|------|-------------|
| `-n, --speakers INT` | Known number of speakers (auto-detected if omitted) |
| `-m, --model SIZE` | Whisper model: `tiny`, `base`, `small`, `medium`, `large` (default), `turbo` |
| `-l, --language CODE` | Source language code, e.g., `ja`, `es` (auto-detected if omitted) |
| `--translate` | Translate foreign audio to English |
| `--no-transcribe` | Skip transcription (diarization only) |

### Analysis

| Flag | Description |
|------|-------------|
| `--profile NAME` | Analysis [profile](profiles.md) (e.g., `business`, `therapy`) |
| `--add-block NAME` | Add extra [block](blocks.md) to profile (repeatable). Requires `--profile`. |
| `--blocks NAME [...]` | Use specific blocks directly, without a profile. Mutually exclusive with `--profile`. |
| `-c, --context TEXT` | Per-run context appended to profile context (e.g., "RSI pharma regulatory meeting") |
| `--no-analyze` | Skip AI analysis entirely |

### Provider

| Flag | Description |
|------|-------------|
| `--provider NAME` | LLM [provider](providers.md): `anthropic` (default) or `ollama` |
| `--llm-model NAME` | Override LLM model name (default depends on provider) |

### Discovery

| Flag | Description |
|------|-------------|
| `--list-profiles` | List available profiles and exit (no audio argument needed) |
| `--list-blocks` | List available blocks and exit (no audio argument needed) |

## Validation rules

- `--blocks` and `--profile` are **mutually exclusive** — use one or the other
- `--add-block` **requires** `--profile`
- If neither `--profile` nor `--blocks` is specified and `--no-analyze` is not set, the tool errors with a message listing available profiles

## Examples

```bash
# Business meeting with per-run context
python src/diarize.py meeting.mp4 -o output/ --profile business -c "Q3 planning"

# Therapy session with local LLM (no API key needed)
python src/diarize.py session.mp4 -o output/ --profile therapy --provider ollama

# Therapy session with a specific Ollama model
python src/diarize.py session.mp4 -o output/ --profile therapy --provider ollama --llm-model phi4:14b

# Profile with extra blocks added
python src/diarize.py meeting.mp4 -o output/ --profile business --add-block emotional_patterns

# Cherry-pick blocks without a profile
python src/diarize.py recording.mp4 -o output/ --blocks session_summary todos key_quotes

# Cherry-pick blocks with ad-hoc context
python src/diarize.py recording.mp4 -o output/ --blocks session_summary key_concepts -c "ML paper discussion"

# Quick transcription, no analysis
python src/diarize.py call.mp4 -o output/ --no-analyze

# Diarization only (fastest — no Whisper, no LLM)
python src/diarize.py call.mp4 -o output/ --no-transcribe

# Translate Japanese meeting to English
python src/diarize.py video.mp4 -o output/ --profile business --translate -l ja

# See what profiles are available
python src/diarize.py --list-profiles

# See what blocks are available
python src/diarize.py --list-blocks
```
