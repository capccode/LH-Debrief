# Providers

## Overview

LH-Debrief supports two LLM providers for the analysis step. Provider selection is **independent** of profile selection — any profile works with any provider.

| Provider | Connection | API key required | Best for |
|----------|-----------|-----------------|----------|
| `anthropic` (default) | Cloud API | Yes | Highest quality analysis |
| `ollama` | Local | No | Offline use, no API costs |

## Anthropic Claude (default)

Uses the Anthropic API with Claude. This is the default when `--provider` is not specified.

```bash
python src/diarize.py meeting.mp4 -o output/ --profile business
python src/diarize.py meeting.mp4 -o output/ --profile business --provider anthropic
```

### Setup

Add to your `.env` file:

```
ANTHROPIC_API_KEY=sk-ant-your_key_here
```

Get a key from: <https://console.anthropic.com/settings/keys>

### Model override

The default model is `claude-opus-4-5-20251101`. Override with:

```bash
python src/diarize.py meeting.mp4 -o output/ --profile business --llm-model claude-sonnet-4-20250514
```

## Ollama (local)

Uses a locally running [Ollama](https://ollama.com) instance. No API key needed — runs fully offline. Ideal for sensitive recordings where data cannot leave the machine.

```bash
python src/diarize.py meeting.mp4 -o output/ --profile therapy --provider ollama
python src/diarize.py meeting.mp4 -o output/ --profile therapy --provider ollama --llm-model phi4:14b
```

### Setup

1. Install Ollama:
   ```bash
   brew install ollama        # macOS
   # or see https://ollama.com/download for other platforms
   ```

2. Pull the default model:
   ```bash
   ollama pull qwen3:8b
   ```

3. Ollama runs automatically in the background after installation. Verify with:
   ```bash
   ollama list
   ```

### Recommended models (16GB RAM)

| Model | Size | Context | Notes |
|-------|------|---------|-------|
| `qwen3:8b` | ~5GB | 32K | Default — best balance of quality and speed |
| `phi4:14b` | ~8.5GB | 16K | Higher quality, tighter RAM fit |

### Custom host

By default, Ollama is expected at `localhost:11434`. Override in your `.env`:

```
OLLAMA_HOST=http://your-host:11434
```

### Error messages

| Error | Meaning | Fix |
|-------|---------|-----|
| "Cannot connect to Ollama" | Ollama is not running | Run `ollama serve` or `brew services start ollama` |
| "Model 'xyz' not found" | Model not pulled yet | Run `ollama pull xyz` |
| "ollama package not installed" | Python package missing | Run `uv add ollama` |
