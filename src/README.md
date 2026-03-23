# LH-Debrief

Diarization + Transcription + AI Analysis for recorded conversations.

## Quick Start

```bash
python src/diarize.py meeting.mp4 -o output/ --profile business
```

## Options

| Flag | Purpose |
|------|---------|
| `-o` | Output directory |
| `-n` | Number of speakers (if known) |
| `-m` | Whisper model (tiny/base/small/medium/large/turbo) |
| `-l` | Source language code (auto-detected if omitted) |
| `-c` | Per-run context appended to profile context |
| `--profile` | Analysis profile (e.g., `business`, `therapy`) |
| `--add-block` | Add extra block to profile (repeatable) |
| `--blocks` | Use specific blocks directly (no profile) |
| `--provider` | LLM provider: `anthropic` (default) or `ollama` |
| `--llm-model` | Override LLM model name |
| `--translate` | Translate foreign audio to English |
| `--no-analyze` | Skip AI analysis |
| `--no-transcribe` | Skip transcription (diarization only) |
| `--list-profiles` | List available profiles and exit |
| `--list-blocks` | List available blocks and exit |

## Examples

```bash
# Business meeting with context
python src/diarize.py meeting.mp4 -o output/ --profile business -c "Q3 planning"

# Therapy session with local Ollama model
python src/diarize.py session.mp4 -o output/ --profile therapy --provider ollama

# Cherry-pick analysis blocks
python src/diarize.py recording.mp4 -o output/ --blocks session_summary action_items todos

# Fast mode (no analysis)
python src/diarize.py meeting.mp4 -o output/ --no-analyze

# Translate Japanese video to English
python src/diarize.py video.mp4 -o output/ --profile business --translate -l ja
```

## Output

Creates a subfolder per recording:

```
output/<meeting-name>/
├── diarization_<name>.json     # Raw speaker segments
├── transcript_<name>.txt       # Speaker-labeled transcript
├── briefing_<name>.md          # Rendered analysis briefing
└── analysis_<name>.json        # Raw LLM analysis JSON
```

## Requirements

**System:** `brew install ffmpeg`

**.env** in workspace root:
```
HF_TOKEN=hf_xxx
ANTHROPIC_API_KEY=sk-ant-xxx   # optional if using --provider ollama
```

Accept pyannote license: https://huggingface.co/pyannote/speaker-diarization-3.1
