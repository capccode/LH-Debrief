# src/ — Python Core Engine

This is the core pipeline that everything else consumes. CLI, API, and Desktop all import from here.

## Modules

| Module | Entry Points | What It Does |
|--------|-------------|-------------|
| `diarize.py` | `main()` | CLI orchestrator — parses args, wires modules together. ~230 lines, no logic of its own. |
| `audio.py` | `diarize()`, `convert_to_wav()`, `get_pipeline()` | FFmpeg conversion, Pyannote 3.1 diarization. CUDA/MPS/CPU auto-detection. NumPy/PyTorch compat patches at top. |
| `transcribe.py` | `get_whisper_model()`, `transcribe_segments()` | Whisper model loading + full-audio transcription mapped to speaker segments. Skips MPS for large models. |
| `analyze.py` | `assemble_prompt()`, `analyze_transcript()` | Builds prompts dynamically from block TOML definitions. Calls `providers.call_llm()`. Returns parsed JSON dict. |
| `render.py` | `render_briefing()` | Generic JSON → markdown. Iterates blocks in profile order, auto-detects value types (string→paragraph, list→bullets, dict→table). |
| `profiles.py` | `load_block()`, `load_profile()`, `resolve_blocks()`, `list_profiles()`, `list_blocks()` | Reads TOML from `blocks/` and `profiles/`. Pure file I/O, no heavy deps. |
| `providers.py` | `call_llm()` | Routes to `_call_anthropic()` or `_call_ollama()`. Defaults: claude-opus-4-5 / qwen3:8b. |

## Data Flow

```
audio file
  → audio.diarize() → speaker segments with timestamps
  → transcribe.transcribe_segments() → segments with text
  → analyze.assemble_prompt() → LLM prompt from blocks
  → providers.call_llm() → raw JSON string
  → analyze.analyze_transcript() → parsed dict
  → render.render_briefing() → markdown briefing + JSON file
```

## Extending (No Python Needed)

**Add a block**: create `blocks/<name>.toml` with `name`, `display_name`, `description`, `prompt`, `json_example`. Reference it in a profile or use `--add-block` / `--blocks`.

**Add a profile**: create `profiles/<name>.toml` with `name`, `description`, `context`, `blocks` (list of block names).

## Commands

```bash
# CLI
python src/diarize.py <audio> -o output/ --profile business
python src/diarize.py --list-profiles
python src/diarize.py --list-blocks

# Tests
uv run python -m pytest tests/test_profiles.py tests/test_providers.py tests/test_analyze.py tests/test_render.py tests/test_cli.py -v

# Lint
ruff check src/
ruff format src/
```

## Important Details

- Compat patches at top of `audio.py` MUST run before other imports (NumPy 2.0 NaN, PyTorch 2.6 weights_only)
- Whisper transcribes full audio then maps to segments (more accurate than segment-by-segment)
- `profiles.py` uses `tomllib` (stdlib) — no extra deps
- `providers.py` lazy-imports `ollama` with try/except so it's optional
- `--blocks` and `--profile` are mutually exclusive; `--add-block` requires `--profile`
