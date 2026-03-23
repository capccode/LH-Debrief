# API Reference

LH-Debrief exposes a REST + WebSocket API for programmatic access to the analysis pipeline.

## Base URL

- Development: `http://localhost:8000`
- The API serves auto-generated interactive docs at `/docs` (Swagger UI)

## Endpoints

### GET /health

Health check for monitoring and load balancers.

**Response:**

```json
{"status": "ok"}
```

**Example:**

```bash
curl http://localhost:8000/health
```

---

### GET /profiles

List all available analysis profiles.

**Response:** `List[ProfileInfo]`

```json
[
  {
    "id": "business",
    "name": "Business Meeting",
    "description": "Corporate meeting analysis — decisions, accountability, stakeholder dynamics",
    "context": "Analyze as a corporate meeting...",
    "blocks": ["session_summary", "decisions", "action_items"]
  }
]
```

**Example:**

```bash
curl http://localhost:8000/profiles
```

---

### GET /blocks

List all available analysis blocks.

**Response:** `List[BlockInfo]`

```json
[
  {
    "name": "session_summary",
    "display_name": "Session Summary",
    "description": "2-3 sentence overview of the conversation",
    "prompt": "...",
    "json_example": "..."
  }
]
```

**Example:**

```bash
curl http://localhost:8000/blocks
```

---

### GET /providers/ollama/models

List locally available Ollama models. Returns an empty array if Ollama is not running.

**Response:** `List[OllamaModel]`

```json
[
  {
    "name": "qwen3:8b",
    "size": 5000000000,
    "modified_at": "2026-03-20T12:00:00Z"
  }
]
```

**Example:**

```bash
curl http://localhost:8000/providers/ollama/models
```

---

### POST /jobs

Start an analysis pipeline job. Accepts multipart form data.

**Parameters:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `file` | File | Yes | Audio or video file to analyze |
| `profile` | string | No | Profile name (mutually exclusive with `blocks`) |
| `blocks` | string | No | Comma-separated block names (mutually exclusive with `profile`) |
| `add_blocks` | string | No | Extra blocks to append (requires `profile`) |
| `provider` | string | No | `"anthropic"` or `"ollama"` (default: `"anthropic"`) |
| `model` | string | No | Model name override |
| `context` | string | No | Additional context for the analysis prompt |
| `output_dir` | string | No | Output directory (default: `"output/"`) |

**Validation rules:**

- `profile` and `blocks` are mutually exclusive — supply one or neither
- `add_blocks` requires `profile`
- `provider` must be `"anthropic"` or `"ollama"`

**Response:** `JobCreateResponse`

```json
{"job_id": "550e8400-e29b-41d4-a716-446655440000", "status": "queued"}
```

**Example:**

```bash
# With a profile
curl -X POST http://localhost:8000/jobs \
  -F "file=@meeting.mp4" \
  -F "profile=business"

# With specific blocks
curl -X POST http://localhost:8000/jobs \
  -F "file=@meeting.mp4" \
  -F "blocks=session_summary,action_items" \
  -F "provider=ollama"

# Diarization only (no profile or blocks)
curl -X POST http://localhost:8000/jobs \
  -F "file=@meeting.mp4"
```

---

### GET /jobs/{job_id}/status

Get job progress.

**Response:** `JobStatus`

```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "running",
  "stage": "transcribing",
  "progress": "Transcribing with Whisper large...",
  "files": ["diarization_meeting.json"],
  "error": null
}
```

| Field | Type | Description |
|-------|------|-------------|
| `status` | string | `"queued"`, `"running"`, `"completed"`, or `"failed"` |
| `stage` | string | Current pipeline stage: `"diarizing"`, `"transcribing"`, `"analyzing"`, `"rendering"`, `"done"` |
| `progress` | string | Human-readable progress message |
| `files` | list | Output filenames available for download |
| `error` | string or null | Error message if `status` is `"failed"` |

**Example:**

```bash
curl http://localhost:8000/jobs/550e8400-e29b-41d4-a716-446655440000/status
```

---

### GET /jobs/{job_id}/output/{filename}

Download an output file. Content-Type is set by file extension:

| Extension | Content-Type |
|-----------|-------------|
| `.md` | `text/markdown` |
| `.json` | `application/json` |
| `.txt` | `text/plain` |

**Example:**

```bash
# Download the briefing
curl http://localhost:8000/jobs/{job_id}/output/briefing_meeting.md

# Download raw analysis JSON
curl http://localhost:8000/jobs/{job_id}/output/analysis_meeting.json
```

Returns `404` if the job or file does not exist. Returns `403` if the path attempts directory traversal.

---

### WS /jobs/{job_id}/logs

WebSocket endpoint for live pipeline log streaming.

**Messages:**

```json
{
  "timestamp": "2026-03-22T14:30:00Z",
  "stage": "transcribe",
  "message": "Loading Whisper large...",
  "status": "running"
}
```

| Field | Type | Description |
|-------|------|-------------|
| `timestamp` | string | ISO 8601 timestamp |
| `stage` | string | Pipeline stage producing the log |
| `message` | string | Log message text |
| `status` | string | `"running"`, `"done"`, or `"error"` |

The connection closes automatically when the job reaches a terminal state (`completed` or `failed`). Connecting to a non-existent job closes the socket with code `4004`.

**Example (Python):**

```python
import asyncio
import websockets
import json

async def stream_logs(job_id: str):
    uri = f"ws://localhost:8000/jobs/{job_id}/logs"
    async with websockets.connect(uri) as ws:
        async for raw in ws:
            msg = json.loads(raw)
            print(f"[{msg['stage']}] {msg['message']}")

asyncio.run(stream_logs("550e8400-e29b-41d4-a716-446655440000"))
```

---

## Python Client Example

```python
import httpx

base = "http://localhost:8000"

# Start a job
with open("meeting.mp4", "rb") as f:
    resp = httpx.post(f"{base}/jobs", files={"file": f}, data={"profile": "business"})
job_id = resp.json()["job_id"]

# Poll until complete
import time
while True:
    status = httpx.get(f"{base}/jobs/{job_id}/status").json()
    print(status["stage"], status["progress"])
    if status["status"] in ("completed", "failed"):
        break
    time.sleep(2)

# Download briefing
for filename in status["files"]:
    if filename.endswith(".md"):
        content = httpx.get(f"{base}/jobs/{job_id}/output/{filename}").text
        print(content)
```
