# Getting Started

## Prerequisites

- Python 3.12+
- [uv](https://docs.astral.sh/uv/) (recommended) or pip
- FFmpeg: `brew install ffmpeg` (macOS) or [ffmpeg.org](https://ffmpeg.org/download.html)
- Hugging Face token — for Pyannote speaker diarization model access

## Installation

```bash
git clone https://github.com/capccode/LH-Debrief.git
cd LH-Debrief

uv sync                      # install all dependencies
# or
uv pip install -e ".[dev]"   # editable install with dev tools
```

## Configuration

Create a `.env` file in the project root:

```bash
# Required — speaker diarization model access
HF_TOKEN=hf_your_token_here

# Required for Anthropic provider (default)
ANTHROPIC_API_KEY=sk-ant-your_key_here

# Optional — skip the API key entirely by using a local model instead
# See the Providers page for Ollama setup
```

You must accept the Pyannote model license before first use:
<https://huggingface.co/pyannote/speaker-diarization-3.1>

## First run

Analyze a business meeting with the default Anthropic provider:

```bash
python src/diarize.py meeting.mp4 -o output/ --profile business
```

Or run fully offline with a local model via [Ollama](providers.md#ollama-local):

```bash
python src/diarize.py meeting.mp4 -o output/ --profile business --provider ollama
```

## What happens

1. **Diarization** — Pyannote 3.1 identifies who spoke when
2. **Transcription** — Whisper converts speech to text, aligned to speaker segments
3. **Analysis** — an LLM extracts structured insights based on your chosen [profile](profiles.md)
4. **Briefing** — results are rendered as a markdown document

## Output

Each run creates a subfolder per recording:

```
output/<meeting-name>/
├── diarization_<name>.json     # Raw speaker segments with timestamps
├── transcript_<name>.txt       # Speaker-labeled transcript
├── briefing_<name>.md          # Formatted analysis briefing
└── analysis_<name>.json        # Raw LLM analysis JSON
```

## Next steps

- **[Profiles](profiles.md)** — choose or create an analysis lens (business, therapy, etc.)
- **[Blocks](blocks.md)** — understand and create individual analysis dimensions
- **[Providers](providers.md)** — switch between Anthropic Claude and local Ollama models
- **[CLI Reference](cli-reference.md)** — full list of flags and examples
