# Getting Started

## Prerequisites

- Python 3.12+
- FFmpeg: `brew install ffmpeg`
- Hugging Face token (for Pyannote speaker diarization)

## Installation

```bash
uv sync                      # install all dependencies
# or
uv pip install -e ".[dev]"   # editable install with dev tools
```

## Configuration

Create a `.env` file in the project root:

```
HF_TOKEN=hf_your_token_here
ANTHROPIC_API_KEY=sk-ant-your_key_here  # optional if using Ollama
```

Accept the Pyannote license: https://huggingface.co/pyannote/speaker-diarization-3.1

## First run

```bash
python src/diarize.py meeting.mp4 -o output/ --profile business
```

## Output

Creates a subfolder per meeting:

```
output/<meeting-name>/
├── transcript_<name>.txt       # Speaker-labeled transcript
├── briefing_<name>.md          # Formatted analysis briefing
├── diarization_<name>.json     # Raw speaker segments
└── analysis_<name>.json        # Raw AI analysis
```
