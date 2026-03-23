# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
# Run full pipeline
python src/diarize.py <audio> -o output/ --profile business
python src/diarize.py <audio> -o output/ --profile therapy --provider ollama

# Diarization + transcription only (no LLM analysis)
python src/diarize.py <audio> -o output/ --no-analyze

# Diarization only (fastest)
python src/diarize.py <audio> -o output/ --no-transcribe

# List available profiles and blocks
python src/diarize.py --list-profiles
python src/diarize.py --list-blocks

# Run tests
uv run python -m pytest tests/ -v

# Lint and format
ruff check src/ tests/
ruff format src/ tests/
```

## Environment Setup

Requires `.env` in workspace root with:
- `HF_TOKEN` — Hugging Face token (must accept pyannote/speaker-diarization-3.1 license)
- `ANTHROPIC_API_KEY` — For Anthropic provider (optional if using Ollama)
- `OLLAMA_HOST` — Optional, defaults to http://localhost:11434

## Architecture

Modular pipeline: **Diarization → Transcription → Analysis → Rendering**

```
diarize.py (CLI orchestrator)
├── audio.py         → ffmpeg conversion, Pyannote diarization, device selection
├── transcribe.py    → Whisper model loading, segment alignment
└── analyze.py       → prompt assembly from blocks, LLM orchestration
      ├── profiles.py  → loads profile/block TOML files, resolves block list
      ├── providers.py → _call_anthropic, _call_ollama (routes via call_llm)
      └── render.py    → generic JSON → markdown briefing using block display_names
```

**diarize.py**: Thin CLI entry point (~230 lines). Parses args, orchestrates pipeline, saves outputs. Contains no audio/whisper/LLM/prompt/rendering logic.

**audio.py**: NumPy/PyTorch compat patches, `convert_to_wav()`, `get_pipeline()`, `diarize()`, `truncate_name()`, `display_results()`. Handles CUDA/MPS/CPU device selection for Pyannote.

**transcribe.py**: `get_whisper_model()`, `transcribe_segments()`, `WhisperSegment`. Handles device selection separately (skips MPS for large Whisper models).

**profiles.py**: `load_block()`, `load_profile()`, `resolve_blocks()`, `list_profiles()`, `list_blocks()`. Reads TOML files from `src/blocks/` and `src/profiles/`.

**analyze.py**: `assemble_prompt()` builds prompts dynamically from block definitions. `analyze_transcript()` calls `call_llm()` and parses JSON response. No hardcoded prompt or schema.

**providers.py**: `call_llm()` routes to `_call_anthropic()` or `_call_ollama()`. Default models: `claude-opus-4-5-20251101` (Anthropic), `qwen3:8b` (Ollama).

**render.py**: `render_briefing()` generates markdown from any analysis dict. Iterates blocks in profile order, uses `display_name` as headings, auto-detects value types (string → paragraph, list[str] → bullets, list[dict] → table).

## Extensibility (no Python needed)

- **Blocks**: TOML files in `src/blocks/` — each defines one analysis dimension (prompt + json_example)
- **Profiles**: TOML files in `src/profiles/` — each defines a block list + context framing
- Add a new block: create `src/blocks/<name>.toml`, reference in profiles or use `--add-block`
- Add a new profile: create `src/profiles/<name>.toml`, use with `--profile`

## Git Conventions

- Do NOT add `Co-Authored-By` lines to commit messages
- Use conventional commits: `feat:`, `fix:`, `docs:`, `chore:`, `refactor:`, `style:`, `test:`, `ci:`
- After completing a feature or fix, run `cz bump` to bump the version based on commit history
- Push tags after bumping: `git push --tags`
- Version is managed by commitizen in `pyproject.toml` — never edit `version` manually

## Key Implementation Details

- NumPy 2.0 and PyTorch 2.6+ compatibility patches at top of `audio.py`
- Whisper transcribes full audio then maps to speaker segments (more accurate than segment-by-segment)
- GPU auto-detected: CUDA → MPS → CPU (Pyannote); CUDA → CPU (Whisper, MPS skipped for large models)
- Default Whisper model is `large` (configurable with `-m`)
- Ollama uses `format="json"` for constrained JSON output
- `--blocks` and `--profile` are mutually exclusive; `--add-block` requires `--profile`

## Output Files

Output is written to `output/YYYY-MM-DD/short-name/`.

| File | Content |
|------|---------|
| `diarization.json` | Raw segments: start, end, speaker, text |
| `transcript.txt` | Human-readable timestamped transcript |
| `briefing.md` | Rendered analysis briefing (section order from profile) |
| `analysis.json` | Raw LLM analysis JSON |
| `metadata.json` | Session metadata for RAG/KG ingestion |
| `entities.json` | Extracted entities and relationships (opt-in via `--extract-entities`) |
