# Quickstart

## CLI — Analyze a meeting in 60 seconds

```bash
# 1. Install
git clone https://github.com/capccode/LH-Debrief.git && cd LH-Debrief
uv sync

# 2. Configure
cp .env.example .env
# Edit .env — add HF_TOKEN and ANTHROPIC_API_KEY (or skip key for Ollama)

# 3. Run
python src/diarize.py meeting.mp4 -o output/ --profile business -c "Q3 planning"
```

Output lands in `output/<meeting-name>/`:

```
briefing_meeting.md          ← the good stuff
transcript_meeting.txt       ← who said what
analysis_meeting.json        ← raw structured data
diarization_meeting.json     ← speaker segments
```

### Using Ollama (no API key needed)

```bash
brew install ollama && ollama pull qwen3:8b
python src/diarize.py meeting.mp4 -o output/ --profile therapy --provider ollama
```

### Quick options

```bash
# Therapy session
python src/diarize.py session.mp4 -o output/ --profile therapy

# Just transcription, no analysis
python src/diarize.py call.mp4 -o output/ --no-analyze

# Pick specific analysis blocks
python src/diarize.py recording.mp4 -o output/ --blocks session_summary action_items todos

# See what's available
python src/diarize.py --list-profiles
python src/diarize.py --list-blocks
```

---

## API — Run as a service

```bash
# 1. Install + configure (same as CLI above)
uv sync
cp .env.example .env  # edit with your keys

# 2. Start the API
uvicorn api.main:app --port 8000

# 3. Use it
curl http://localhost:8000/profiles     # list profiles
curl http://localhost:8000/blocks       # list blocks
```

### Analyze a file via API

```bash
curl -X POST http://localhost:8000/jobs \
  -F "file=@meeting.mp4" \
  -F "profile=business" \
  -F "context=Q3 planning"

# Returns: {"job_id": "abc123", "status": "queued"}

# Poll for completion
curl http://localhost:8000/jobs/abc123/status

# Download the briefing
curl http://localhost:8000/jobs/abc123/output/briefing_meeting.md
```

Interactive API docs at [localhost:8000/docs](http://localhost:8000/docs).

---

## Desktop App — Click and go

For users who don't want a terminal:

```bash
# 1. Prerequisites (one-time)
brew install ffmpeg ollama uv
ollama pull qwen3:8b

# 2. Build the app
cd desktop && npm install && npm run make

# 3. Open LH-Debrief.app
```

First launch shows a setup wizard. After that: drop a file, pick a profile, click Run.
