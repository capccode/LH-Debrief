# AGENTS.md — LH-Debrief Project Guide

## What This Project Is

LH-Debrief is a speaker diarization, transcription, and AI analysis tool for recorded conversations. It takes audio/video files and produces structured briefings with configurable analysis dimensions.

**Three interfaces, same core:**
- **CLI** (`src/diarize.py`) — power user, scriptable
- **API** (`api/`) — FastAPI backend, deployable on Tailscale/AWS
- **Desktop** (`desktop/`) — Electron app wrapping API + frontend, for non-technical users

## Project Map

```
LH-Debrief/
├── src/                    # Python core — the engine everything runs on
│   ├── diarize.py          # CLI entry point (thin orchestrator)
│   ├── audio.py            # FFmpeg conversion, Pyannote diarization
│   ├── transcribe.py       # Whisper transcription + segment alignment
│   ├── analyze.py          # Prompt assembly from blocks, LLM orchestration
│   ├── render.py           # Generic JSON → markdown briefing
│   ├── profiles.py         # TOML profile/block loading
│   ├── providers.py        # LLM routing (Anthropic + Ollama)
│   ├── blocks/             # 13 TOML analysis dimension definitions
│   └── profiles/           # 2 TOML profile configs (business, therapy)
├── api/                    # FastAPI backend — wraps src/ as REST + WebSocket API
│   ├── main.py             # App + routes (8 endpoints)
│   ├── jobs.py             # Background pipeline jobs + in-memory store
│   └── schemas.py          # Pydantic models
├── web/                    # Next.js + TypeScript frontend
│   └── src/
│       ├── app/            # Layout + main page (two-panel dashboard)
│       ├── components/     # 7 React components
│       └── lib/            # API client + TypeScript types
├── desktop/                # Electron wrapper (macOS .app)
│   └── src/
│       ├── main.ts         # Spawns FastAPI, loads Next.js in window
│       ├── settings.ts     # macOS Keychain via safeStorage
│       ├── ollama.ts       # Ollama detection
│       └── pages/setup.html # First-launch wizard
├── tests/                  # pytest — 64 tests covering src/ and api/
├── docs/                   # MkDocs documentation (12 pages)
├── CLAUDE.md               # Claude Code instructions (commands, architecture, conventions)
└── pyproject.toml          # Python deps, ruff, pytest config
```

## How the Pieces Connect

```
Desktop App (Electron)
    │ spawns                  │ loads
    ▼                         ▼
FastAPI (api/)           Next.js (web/)
    │ imports                 │ fetches
    ▼                         ▼
Python Core (src/)       FastAPI REST + WS
```

The **Python core** (`src/`) is the foundation. Everything else is a consumer:
- CLI calls core directly
- API calls core via lazy imports in background threads
- Frontend talks to API via REST/WebSocket
- Desktop bundles API + Frontend into a native app

## Quick Commands

```bash
# Run the CLI
python src/diarize.py meeting.mp4 -o output/ --profile business

# Run the API
uvicorn api.main:app --reload --port 8000

# Run the frontend
cd web && npm run dev

# Run the desktop app (dev mode — needs API + frontend running)
cd desktop && npm run start

# Run tests
uv run python -m pytest tests/ -v

# Lint
ruff check src/ api/ tests/
```

## Key Conventions

- **No `Co-Authored-By`** lines in commits
- **Conventional commits**: `feat:`, `fix:`, `docs:`, `refactor:`, `test:`, `ci:`
- **uv** for Python dependency management (not pip)
- **Extensibility via TOML**: blocks in `src/blocks/`, profiles in `src/profiles/` — no Python needed
- **Lazy imports**: `api/jobs.py` imports torch/whisper/pyannote inside `_run_pipeline_sync()`, not at module level — keeps API startup fast

## Deployment Targets

1. **Standalone API** — `uvicorn api.main:app --host 0.0.0.0 --port 8000` on Tailscale/AWS
2. **Desktop app** — `cd desktop && npm run make` → produces macOS `.dmg`

## Where to Look

| I want to... | Start here |
|-------------|------------|
| Add an analysis dimension | `src/blocks/` — create a TOML file |
| Add an analysis profile | `src/profiles/` — create a TOML file |
| Add an LLM provider | `src/providers.py` — add `_call_<name>()` |
| Add an API endpoint | `api/main.py` — add route + schema in `api/schemas.py` |
| Add a frontend component | `web/src/components/` |
| Modify CLI flags | `src/diarize.py` — argparse section |
| Fix GPU/device issues | `src/audio.py` (Pyannote) or `src/transcribe.py` (Whisper) |
| Understand the prompt | `src/analyze.py:assemble_prompt()` + `src/blocks/*.toml` |
