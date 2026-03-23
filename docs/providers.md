# Providers

## Overview

LH-Debrief supports two LLM providers for the analysis step. Provider selection is independent of profile selection.

## Anthropic Claude (default)

Uses the Anthropic API. Requires an API key.

```bash
python src/diarize.py meeting.mp4 -o output/ --profile business
python src/diarize.py meeting.mp4 -o output/ --profile business --provider anthropic
```

### Setup

Add to `.env`:
```
ANTHROPIC_API_KEY=sk-ant-your_key_here
```

## Ollama (local)

Uses a locally running Ollama instance. No API key needed — runs fully offline.

```bash
python src/diarize.py meeting.mp4 -o output/ --profile therapy --provider ollama
python src/diarize.py meeting.mp4 -o output/ --profile therapy --provider ollama --llm-model phi4:14b
```

### Setup

1. Install Ollama: `brew install ollama`
2. Pull a model: `ollama pull qwen3:8b`
3. Ollama runs automatically in the background

### Recommended models (16GB RAM)

| Model | Size | Context | Notes |
|-------|------|---------|-------|
| `qwen3:8b` | ~5GB | 32K | Best balance of quality and speed |
| `phi4:14b` | ~8.5GB | 16K | Higher quality, tighter RAM fit |

### Custom host

By default, Ollama is expected at `localhost:11434`. Override with:
```
OLLAMA_HOST=http://your-host:11434
```
