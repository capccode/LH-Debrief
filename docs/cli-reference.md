# CLI Reference

<!-- TODO: Update as new flags are implemented -->

## Usage

```bash
python src/diarize.py <audio> [options]
```

## Arguments

| Argument | Description |
|----------|-------------|
| `audio` | Path to audio/video file (wav, mp3, m4a, mp4, etc.) |

## Options

### Output

| Flag | Description |
|------|-------------|
| `-o, --output PATH` | Output directory |

### Audio processing

| Flag | Description |
|------|-------------|
| `-n, --speakers INT` | Known number of speakers |
| `-m, --model SIZE` | Whisper model: tiny, base, small, medium, large (default), turbo |
| `-l, --language CODE` | Source language code (auto-detected if omitted) |
| `--translate` | Translate foreign audio to English |
| `--no-transcribe` | Skip transcription (diarization only) |

### Analysis

| Flag | Description |
|------|-------------|
| `--profile NAME` | Analysis profile (e.g., business, therapy) |
| `--add-block NAME` | Add block(s) to profile (repeatable) |
| `--blocks NAME [...]` | Use specific blocks (no profile) |
| `-c, --context TEXT` | Per-run context (appended to profile context) |
| `--no-analyze` | Skip AI analysis |

### Provider

| Flag | Description |
|------|-------------|
| `--provider NAME` | LLM provider: anthropic (default) or ollama |
| `--llm-model NAME` | Override LLM model name |

### Discovery

| Flag | Description |
|------|-------------|
| `--list-profiles` | List available profiles and exit |
| `--list-blocks` | List available blocks and exit |

## Examples

```bash
# Business meeting with context
python src/diarize.py meeting.mp4 -o output/ --profile business -c "Q3 planning"

# Therapy session with local LLM
python src/diarize.py session.mp4 -o output/ --profile therapy --provider ollama

# Quick transcription, no analysis
python src/diarize.py call.mp4 -o output/ --no-analyze

# Cherry-pick analysis blocks
python src/diarize.py recording.mp4 -o output/ --blocks session_summary todos key_quotes

# Translate Japanese meeting
python src/diarize.py video.mp4 -o output/ --profile business --translate -l ja
```
