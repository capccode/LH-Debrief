# api/ — FastAPI Backend

REST + WebSocket API wrapping the Python core (`src/`). Serves two deployment targets: embedded in Electron desktop app AND standalone on Tailscale/AWS.

## Running

```bash
# Development (auto-reload)
uvicorn api.main:app --reload --port 8000

# Production
uvicorn api.main:app --host 0.0.0.0 --port 8000

# Interactive API docs
open http://localhost:8000/docs
```

## Endpoints

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/health` | Health check — returns `{"status": "ok"}` |
| GET | `/profiles` | List all analysis profiles with metadata |
| GET | `/blocks` | List all analysis blocks with metadata |
| GET | `/providers/ollama/models` | Proxy Ollama's model list (empty array if not running) |
| POST | `/jobs` | Upload file + start pipeline (multipart form) |
| GET | `/jobs/{id}/status` | Job progress, stage, output file list |
| GET | `/jobs/{id}/output/{filename}` | Serve output files (markdown, JSON, text) |
| WS | `/jobs/{id}/logs` | Live pipeline log streaming |

## Architecture

```
main.py          → FastAPI app, routes, CORS, WebSocket handler
jobs.py          → JobStore (in-memory dict), run_pipeline (async→thread), _run_pipeline_sync
schemas.py       → Pydantic models: ProfileInfo, BlockInfo, JobStatus, LogMessage, etc.
```

### How it imports src/

`sys.path.insert(0, "../../src")` at the top of `main.py` and `jobs.py`. Heavy modules (torch, whisper, pyannote) are **lazy-imported inside `_run_pipeline_sync()`** — this keeps API startup fast and tests lightweight.

### Job lifecycle

1. `POST /jobs` → saves upload to tempdir → creates `JobRecord` → fires `asyncio.create_task(run_pipeline(...))`
2. `run_pipeline()` → dispatches `_run_pipeline_sync()` to thread pool via `asyncio.to_thread()`
3. Pipeline thread calls `diarize()` → `transcribe_segments()` → `analyze_transcript()` → `render_briefing()`
4. Cross-thread logging via `asyncio.run_coroutine_threadsafe(store.add_log(...))`
5. WebSocket clients poll `store.get_logs(offset)` every 300ms

### Validation rules (same as CLI)

- `profile` and `blocks` are mutually exclusive (400 error)
- `add_blocks` requires `profile` (400 error)
- `provider` must be `anthropic` or `ollama` (400 error)

## Files

| File | Lines | What It Does |
|------|-------|-------------|
| `main.py` | ~240 | App setup, all route handlers, WebSocket logs |
| `jobs.py` | ~240 | JobStore, JobRecord dataclass, pipeline runner |
| `schemas.py` | ~50 | 7 Pydantic response models |

## Tests

```bash
uv run python -m pytest tests/test_api.py -v
```

25 tests covering: health, profiles, blocks, Ollama proxy, job creation, validation, status, output serving, path traversal protection, WebSocket.

All tests mock the pipeline (`_run_pipeline_sync`) — no GPU or models needed.

## Key Design Decisions

- **In-memory job store** — fine for single-user. Multi-user would need Redis/DB.
- **Single worker** — pipeline is GPU-intensive, no concurrent workloads.
- **CORS allow-all** — appropriate for dev and single-user Tailscale. Tighten for public deployment.
- **Path traversal protection** — `is_relative_to()` check on output file serving.
