# Frontend UI — Design Spec

> **Status:** Future work. This is a standalone project that consumes the same core engine as the CLI.

## Goal

A simple, user-friendly web UI for non-technical users (therapist buddy) to upload audio files, select profiles/blocks/providers, watch processing, and view output — without touching a terminal.

## Design Language

- Dark theme inspired by Claude Code's terminal aesthetic (dark background, colored status lines, monospace accents)
- Clean, modern layout — not a terminal emulator, but evokes the same feel
- Left panel for controls, right panel for content

## Layout

```
┌─────────────────────┬──────────────────────────────────────────────┐
│                     │                                              │
│   [LH-Debrief]      │   File Viewer / MD Preview                   │
│   ─────────────     │                                              │
│                     │   (rendered markdown briefing, transcript,   │
│   INPUT             │    or raw JSON — selected from output tree)  │
│   ┌───────────────┐ │                                              │
│   │ Drop files or │ │   Toggle: Rendered ⟷ Raw                    │
│   │ click to add  │ │                                              │
│   └───────────────┘ │                                              │
│   meeting1.mp4  ✕   │                                              │
│   session2.wav  ✕   │                                              │
│                     │                                              │
│   CONTEXT (-c)      │                                              │
│   ┌───────────────┐ │                                              │
│   │ Free text     │ │                                              │
│   └───────────────┘ │                                              │
│                     │──────────────────────────────────────────────│
│   OUTPUT FOLDER     │                                              │
│   📁 ~/output/      │   Processing Log                             │
│                     │                                              │
│   PROFILE           │   ✓ Converting mp4 → wav                    │
│   [therapy     ▾]   │   ✓ Loading Pyannote 3.1                    │
│                     │   ✓ Speaker diarization (3 speakers)        │
│   BLOCKS            │   ⟳ Transcribing with Whisper large...      │
│   ☑ session_summary │                                              │
│   ☑ decisions       │                                              │
│   ☑ action_items    │                                              │
│   ☐ methodology_n.. │                                              │
│                     │                                              │
│   PROVIDER          │   OUTPUT FILES                               │
│   ○ Anthropic       │   📁 session-notes/                          │
│   ● Ollama          │     📄 transcript_session-notes.txt          │
│                     │     📄 briefing_session-notes.md   ← viewing │
│   MODEL             │     📄 diarization_session-notes.json        │
│   [qwen3:8b    ▾]   │     📄 analysis_session-notes.json           │
│                     │                                              │
│   [▶ Run Analysis]  │                                              │
│                     │                                              │
└─────────────────────┴──────────────────────────────────────────────┘
```

### Left Panel — Controls

**Input section:**
- Drag-and-drop zone or file picker for audio/video files
- Support multiple files as a batch queue
- Each file shows status: queued → processing → done
- ✕ button to remove from queue
- Context text input (maps to `-c` flag)
- Output folder picker

**Profile selector:**
- Dropdown populated from `src/profiles/*.toml`
- On selection, shows a preview card with:
  - Profile `name` and `description`
  - Profile `context` (the lens)
  - List of included blocks
- Selecting a profile auto-checks its blocks in the block list

**Block selector:**
- Checkboxes for all available blocks (from `src/blocks/*.toml`)
- Profile blocks shown as locked/greyed (can't uncheck — they come from the profile)
- Additional blocks shown below a divider with ✕ to remove
- Info icon (ⓘ) next to each block — click/hover shows:
  - `display_name`
  - `description`
  - Expected output format (from `json_example`)

```
☑ action_items  ⓘ
  ┌─────────────────────────────────────────┐
  │ Extract action items with owners and    │
  │ due dates                               │
  │                                         │
  │ Output: list of {owner, action, due}    │
  └─────────────────────────────────────────┘
```

**Provider selector:**
- Radio buttons: Anthropic / Ollama
- When Anthropic selected: no model dropdown needed (uses default)
- When Ollama selected: model dropdown auto-populated from `localhost:11434/api/tags`
- Model override input for Anthropic (optional, for power users)

**Run button:**
- Disabled until at least one file + profile/blocks selected
- Shows progress state while running

### Right Panel — Content

**Top section: File Viewer / MD Preview**
- Renders selected output file
- Markdown files (briefing) rendered with proper formatting
- JSON files shown with syntax highlighting
- Text files (transcript) shown with monospace formatting
- Toggle button: Rendered ⟷ Raw

**Bottom section (split):**

**Processing Log:**
- Live streaming log output from the backend
- Shows each pipeline stage with status icons (✓ done, ⟳ running, ✕ error)
- Scrolls automatically, stays pinned to bottom

**Output File Tree:**
- Shows output directory structure
- Files appear as they're generated (live updates)
- Click a file to view it in the preview pane above
- Currently viewing file highlighted

## Batch Queue Behavior

When multiple files are selected:
- Show as a queue list in the input section
- Process sequentially (diarization is GPU-intensive)
- Each file shows individual status
- Output tree updates per file as they complete
- User can view completed outputs while others are still processing

## Data Flow

```
Next.js Frontend (standalone)
    │
    ├── REST → FastAPI Backend
    │         ├── GET  /profiles          → reads src/profiles/*.toml
    │         ├── GET  /blocks            → reads src/blocks/*.toml
    │         ├── GET  /providers/ollama/models → proxies localhost:11434/api/tags
    │         ├── POST /jobs              → uploads file, starts pipeline
    │         ├── GET  /jobs/{id}/status  → job progress
    │         └── GET  /jobs/{id}/output/{file} → serve output files
    │
    ├── WebSocket → FastAPI Backend
    │         └── WS /jobs/{id}/logs     → live pipeline log streaming
    │
    └── Calls same Python core modules:
          ├── audio.py → diarize
          ├── transcribe.py → transcription
          ├── analyze.py → LLM analysis
          └── render.py → markdown briefing
```

## Tech Stack

### Frontend

| Layer | Tech | Purpose |
|-------|------|---------|
| Framework | Next.js + TypeScript | SSR for initial load, client-side for interactive UI |
| Styling | Tailwind CSS (dark mode) | `darkMode: 'class'`, matches Claude Code aesthetic |
| MD rendering | `react-markdown` + `remark-gfm` | Render briefing files with tables, lists, code blocks |
| File upload | `react-dropzone` | Drag-and-drop zone for audio/video files |
| WebSocket | Native browser WS | Live log streaming from FastAPI |
| Syntax highlight | `react-syntax-highlighter` | JSON file viewer |

### Backend API

| Layer | Tech | Purpose |
|-------|------|---------|
| Framework | FastAPI | Thin wrapper around Python core modules |
| WebSocket | FastAPI WebSocket | Stream processing logs to frontend |
| File handling | `python-multipart` | Handle file uploads |
| Background jobs | `asyncio` / background tasks | Run pipeline without blocking API |
| API docs | Auto-generated OpenAPI | Free docs at `/docs` |

### API Endpoints

| Method | Endpoint | Request | Response |
|--------|----------|---------|----------|
| `GET` | `/profiles` | — | `[{name, display_name, description, context, blocks}]` |
| `GET` | `/blocks` | — | `[{name, display_name, description, prompt, json_example}]` |
| `GET` | `/providers/ollama/models` | — | `[{name, size, modified}]` — proxied from Ollama |
| `POST` | `/jobs` | `multipart: file, profile, blocks[], provider, model, context` | `{job_id, status: "queued"}` |
| `GET` | `/jobs/{id}/status` | — | `{status, progress, files[]}` |
| `GET` | `/jobs/{id}/output/{filename}` | — | File content (text, json, or markdown) |
| `WS` | `/jobs/{id}/logs` | — | Stream of `{timestamp, stage, message, status}` |

### Project Structure

```
LH-Debrief/
├── src/                    # Python core modules (existing)
│   ├── audio.py
│   ├── transcribe.py
│   ├── analyze.py
│   ├── render.py
│   ├── profiles.py
│   ├── providers.py
│   ├── blocks/
│   └── profiles/
├── api/                    # FastAPI backend (new)
│   ├── main.py             # App + routes
│   ├── jobs.py             # Job queue + background processing
│   └── schemas.py          # Pydantic models for API responses
├── web/                    # Next.js frontend (new, standalone)
│   ├── app/
│   │   ├── layout.tsx      # Dark theme shell
│   │   └── page.tsx        # Main dashboard
│   ├── components/
│   │   ├── FileUpload.tsx
│   │   ├── ProfileSelector.tsx
│   │   ├── BlockSelector.tsx
│   │   ├── ProviderSelector.tsx
│   │   ├── ProcessingLog.tsx
│   │   ├── OutputTree.tsx
│   │   └── FileViewer.tsx
│   ├── tailwind.config.ts
│   ├── package.json
│   └── tsconfig.json
├── desktop/                # Electron wrapper (new)
│   ├── main.ts             # Electron main process — spawns FastAPI, opens window
│   ├── preload.ts          # Bridge between renderer and main process
│   ├── settings.ts         # First-launch setup + credential storage
│   ├── forge.config.ts     # Electron Forge build config
│   ├── package.json
│   └── assets/
│       └── icon.icns       # macOS app icon
├── diarize.py              # CLI entry point (existing)
└── pyproject.toml
```

## Electron Desktop App

### Overview

Electron wraps the Next.js frontend + FastAPI backend into a native macOS `.app`. The user double-clicks `LH-Debrief.app` — no terminal, no browser, no commands.

```
LH-Debrief.app (Electron)
    │
    ├── Electron main process
    │   ├── Spawns FastAPI as child process
    │   ├── Loads Next.js frontend in app window
    │   └── Manages credentials via macOS Keychain
    │
    └── Connects to Ollama (external, already running on host)
```

### First Launch — Setup Screen

On first launch (no saved credentials), the app shows a setup screen before the main UI:

```
┌─────────────────────────────────────┐
│  Welcome to LH-Debrief             │
│                                     │
│  Provider:                          │
│  ○ Local (Ollama)                   │
│  ○ Anthropic Claude                 │
│                                     │
│  [If Anthropic selected:]           │
│  API Key: [sk-ant-••••••••]         │
│                                     │
│  [If Ollama selected:]              │
│  Status: ✓ Ollama running           │
│  Model:  [qwen3:8b ▾]              │
│                                     │
│  [Save & Continue]                  │
└─────────────────────────────────────┘
```

### Credential Storage

API keys are stored in **macOS Keychain** via Electron's `safeStorage` — encrypted at rest, unlocked by the user's macOS login. Never stored in plain text files.

```typescript
// First launch — encrypt and store
import { safeStorage } from 'electron'
const encrypted = safeStorage.encryptString(apiKey)
store.set('anthropic_key', encrypted.toString('base64'))

// Every launch after — decrypt and pass to FastAPI
const encrypted = Buffer.from(store.get('anthropic_key'), 'base64')
const apiKey = safeStorage.decryptString(encrypted)
// Set as env var for FastAPI child process
```

Settings are persisted — user enters credentials once, never again. A settings page in the app allows changing provider, model, or API key later.

### Ollama Detection

On launch, the app checks `localhost:11434` for a running Ollama instance:
- **Running** → show available models in dropdown (from `/api/tags`)
- **Not running** → show "Start Ollama" message with instructions
- **No models pulled** → show "Pull a model" with suggested command

### Build & Distribution

Using [Electron Forge](https://www.electronforge.io/):

```bash
cd desktop/
npm run make     # Produces LH-Debrief.app (macOS)
npm run package  # Produces .dmg for distribution
```

The `.dmg` is what you'd hand your buddy — he drags it to Applications, done.

### Prerequisites (installed once on buddy's machine)

1. **Ollama**: `brew install ollama && ollama pull qwen3:8b`
2. **FFmpeg**: `brew install ffmpeg`
3. **Python + uv**: for FastAPI backend (bundled or pre-installed)

Note: A future version could bundle Python + FFmpeg inside the `.app` to eliminate prerequisites entirely, but that adds significant build complexity.

### Privacy Note

For therapy use cases, **local-only mode (Ollama) is the recommended default**. All processing stays on-device — no audio, transcripts, or analysis ever leave the machine. This is critical for session confidentiality.

## What's NOT in scope (for v1)

- User authentication
- Cloud storage / remote files
- Real-time collaborative viewing
- Mobile layout
- Custom theme editor
- Profile/block TOML editing from the UI (edit files directly for now)
- Batch queue management UI (v1 processes one file at a time; batch queue is v2)
- Bundling Python/FFmpeg inside the Electron app (requires pre-install for now)
