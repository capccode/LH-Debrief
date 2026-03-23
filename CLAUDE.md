# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
# Run full pipeline (from workspace root)
python tools/meeting-intel/src/diarize.py <audio.wav> -o output/ -c "domain context"

# Diarization + transcription only (no Claude analysis)
python tools/meeting-intel/src/diarize.py <audio.wav> -o output/ --no-analyze

# Diarization only (fastest)
python tools/meeting-intel/src/diarize.py <audio.wav> -o output/ --no-transcribe

# Lint and format
ruff check tools/meeting-intel/
ruff format tools/meeting-intel/

# Type check
pyright tools/meeting-intel/
```

## Environment Setup

Requires `.env` in workspace root with:
- `HF_TOKEN` - Hugging Face token (must accept pyannote/speaker-diarization-3.1 license)
- `ANTHROPIC_API_KEY` - For Claude analysis

## Architecture

Three-stage pipeline: **Diarization → Transcription → Analysis**

```
diarize.py (orchestrator)
├── Pyannote 3.1 → speaker segments with timestamps
├── Whisper → speech-to-text mapped to segments
└── analyze.py → Claude extracts structured insights
```

**diarize.py** (`src/diarize.py:198-280`): Main entry point. Handles CLI args, runs diarization via `diarize()`, optionally transcribes via `transcribe_segments()`, saves JSON/txt outputs, and calls `analyze_transcript()`.

**analyze.py** (`src/analyze.py:34-134`): Sends transcript to Claude, returns `MeetingAnalysis` TypedDict with executive_summary, decisions, action_items, key_concepts, open_questions, follow_ups. The `save_briefing()` function formats this as markdown.

## Key Implementation Details

- NumPy 2.0 and PyTorch 2.6+ compatibility patches at top of `diarize.py`
- Whisper transcribes full audio then maps to speaker segments (more accurate than segment-by-segment)
- GPU auto-detected and used when available
- Default Whisper model is `large` (configurable with `-m`)
- Claude model: `claude-opus-4-5-20251101`

## Output Files

| File | Content |
|------|---------|
| `*_diarization.json` | Raw segments: start, end, speaker, text |
| `*_transcript.txt` | Human-readable timestamped transcript |
| `*_briefing.md` | Executive summary + structured insights |
| `*_analysis.json` | Raw Claude analysis JSON |
