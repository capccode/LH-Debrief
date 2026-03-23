# Meeting Intel

Diarization + Transcription + AI Analysis for meeting recordings.

## Quick Start

```bash
python tools/meeting-intel/src/diarize.py meeting.mp4 -o tools/meeting-intel/output/ -c "your meeting context"
```

## Options

| Flag | Purpose |
|------|---------|
| `-o` | Output directory |
| `-n` | Number of speakers (if known) |
| `-c` | Domain context for better analysis |
| `-m` | Whisper model (tiny/base/small/medium/large/turbo) |
| `-l` | Source language code (auto-detected if omitted) |
| `--translate` | Translate foreign audio to English |
| `--no-analyze` | Skip Claude analysis |
| `--no-transcribe` | Skip transcription (diarization only) |

## Examples

```bash
# Full pipeline with context
python tools/meeting-intel/src/diarize.py meeting.mp4 -o tools/meeting-intel/output/ -c "RSI pharma regulatory"

# Translate Japanese video to English
python tools/meeting-intel/src/diarize.py video.mp4 -o tools/meeting-intel/output/ --translate

# Fast mode (no Claude analysis)
python tools/meeting-intel/src/diarize.py meeting.mp4 -o tools/meeting-intel/output/ --no-analyze
```

## Output

Creates a subfolder per meeting (using truncated filename):

```
tools/meeting-intel/output/
└── rsi-meeting/
    ├── transcript_rsi-meeting.txt
    ├── briefing_rsi-meeting.md
    ├── diarization_rsi-meeting.json
    └── analysis_rsi-meeting.json
```

| File | Content |
|------|---------|
| `transcript_{name}.txt` | Speaker-labeled transcript |
| `briefing_{name}.md` | Executive summary, actions, decisions |
| `diarization_{name}.json` | Raw segment data |
| `analysis_{name}.json` | Raw Claude analysis |

## Requirements

**System:** `brew install ffmpeg` (or equivalent)

**.env** in workspace root:
```
HF_TOKEN=hf_xxx
ANTHROPIC_API_KEY=sk-ant-xxx
```

Accept pyannote license: https://huggingface.co/pyannote/speaker-diarization-3.1
