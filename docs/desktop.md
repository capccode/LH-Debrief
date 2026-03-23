# Desktop App

The Electron desktop app wraps the FastAPI + Next.js stack into a native macOS application. Designed for non-technical users who need a click-to-run experience.

## Prerequisites

On the target machine:

- **macOS**
- **FFmpeg**: `brew install ffmpeg`
- **Ollama** (recommended): `brew install ollama && ollama pull qwen3:8b`
- **Python 3.12+** with uv: `brew install uv`

## Development

```bash
cd desktop/
npm install
npm run build    # Compile TypeScript
```

Start the app (requires FastAPI + Next.js running separately in development):

```bash
npm run start
```

## Building for Distribution

```bash
cd desktop/
npm run make     # Produces LH-Debrief.app in out/
npm run package  # Produces .dmg for distribution
```

The `.dmg` is what you hand to users — they drag it to Applications and run it.

The packaged app bundles the full Python backend (`api/`, `src/`, `pyproject.toml`, `uv.lock`) inside its resources, so users do not need to clone the repo.

## How It Works

1. User double-clicks **LH-Debrief.app**
2. Electron finds an available port (starting at 8000)
3. Spawns FastAPI as a child process (`uv run uvicorn api.main:app`)
4. Polls `/health` every 500ms until the API responds (30s timeout)
5. Opens a window loading the Next.js frontend
6. On quit, sends SIGTERM to FastAPI and waits up to 5 seconds before force-killing

## First Launch

On first launch, a setup screen appears:

- **Select provider**: Ollama (recommended for privacy) or Anthropic
- **Enter API key**: Required if using Anthropic as the provider
- **Enter Hugging Face token**: Required for speaker diarization (Pyannote model access)
- Settings are saved and the app proceeds to the main interface

## Security

- **Encrypted credentials**: API keys are stored via macOS Keychain through Electron's `safeStorage` API — encrypted at rest, not in plaintext config files
- **Local-only networking**: FastAPI binds to `127.0.0.1` only — not exposed to the network
- **On-device processing**: Using Ollama keeps all data local — no audio or transcripts leave the machine. Critical for sensitive recordings like therapy sessions.

## Architecture

```
LH-Debrief.app
├── Electron main process
│   ├── Spawns: uv run uvicorn api.main:app --port {dynamic}
│   ├── Window: loads http://localhost:3000 (Next.js)
│   └── Settings: electron-store + safeStorage
├── Bundled resources
│   ├── api/          (FastAPI backend)
│   ├── src/          (pipeline modules)
│   ├── pyproject.toml
│   └── uv.lock
└── External: Ollama at localhost:11434
```

## IPC Channels

The Electron main process exposes these IPC handlers to the renderer:

| Channel | Direction | Description |
|---------|-----------|-------------|
| `get-settings` | Renderer → Main | Returns current app settings |
| `save-settings` | Renderer → Main | Stores provider, model, API keys |
| `is-first-launch` | Renderer → Main | Check if setup wizard should show |
| `get-ollama-status` | Renderer → Main | Check if Ollama daemon is reachable |

## Troubleshooting

**App shows "Backend failed to start"**: The FastAPI process did not respond to `/health` within 30 seconds. Check that Python 3.12+ and uv are installed, and that no other process is using port 8000.

**Diarization fails**: Ensure `HF_TOKEN` is set and you have accepted the [pyannote/speaker-diarization-3.1](https://huggingface.co/pyannote/speaker-diarization-3.1) license on Hugging Face.

**Ollama models not showing**: Verify Ollama is running (`ollama list`). The app checks `localhost:11434` by default.
