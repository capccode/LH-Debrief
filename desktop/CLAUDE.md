# desktop/ — Electron Desktop App

Native macOS app for non-technical users. Double-click → everything works. No terminal, no browser.

## Running (Development)

```bash
cd desktop
npm install          # first time
npm run build        # compile TypeScript
npm run start        # launch (needs API + frontend running separately)
```

For the full dev stack:
```bash
# Terminal 1: FastAPI
uvicorn api.main:app --reload --port 8000

# Terminal 2: Next.js
cd web && npm run dev

# Terminal 3: Electron
cd desktop && npm run start
```

## Building for Distribution

```bash
cd desktop
npm run make         # → LH-Debrief.app (macOS)
npm run package      # → .dmg for distribution
```

Hand the `.dmg` to the user — they drag to Applications, done.

## Architecture

```
LH-Debrief.app
├── main.ts          → Main process (Electron)
│   ├── Spawns FastAPI via `uv run uvicorn api.main:app --port {dynamic}`
│   ├── Polls /health until API is ready (30s timeout)
│   ├── Opens BrowserWindow loading Next.js at localhost:3000
│   └── Kills FastAPI child process on quit
├── settings.ts      → electron-store + safeStorage (macOS Keychain)
├── ollama.ts        → Checks localhost:11434 for running Ollama
├── preload.ts       → contextBridge: getSettings, saveSettings, isFirstLaunch, getOllamaStatus
└── pages/setup.html → First-launch setup wizard
```

## Files

| File | Purpose |
|------|---------|
| `src/main.ts` | Main process — spawns API, creates window, IPC handlers, lifecycle |
| `src/settings.ts` | Credential storage (safeStorage encryption), app settings (electron-store) |
| `src/ollama.ts` | Ollama detection at localhost:11434 |
| `src/preload.ts` | contextBridge exposing electronAPI to setup page |
| `src/pages/setup.html` | Self-contained first-launch setup wizard |
| `forge.config.ts` | Electron Forge build config (DMG + ZIP makers) |

## Startup Sequence

1. `app.on('ready')` → check `isFirstLaunch()`
2. If first launch → show `setup.html` (provider selection, API key, HF token)
3. Find available port (scan from 8000 upward)
4. Spawn FastAPI: `uv run uvicorn api.main:app --port {port} --host 127.0.0.1`
5. Poll `http://127.0.0.1:{port}/health` until ready
6. Create BrowserWindow → load Next.js frontend
7. On quit → SIGTERM child process, wait 5s, SIGKILL if needed

## Credential Storage

- API keys encrypted via `safeStorage.encryptString()` → stored as base64 in electron-store
- Decrypted at startup → passed as env vars to FastAPI child process
- Never stored in plain text
- Default provider: **Ollama** (privacy-first for therapy use case)

## Error Handling

- FastAPI fails to start → error dialog with Retry/Quit
- Health check timeout → "Backend taking too long" dialog
- Ollama not running → non-fatal (frontend handles gracefully)
- Setup closed without completing → app quits

## Prerequisites (Target Machine)

- macOS
- FFmpeg: `brew install ffmpeg`
- Python 3.12+ with uv: `brew install uv`
- Ollama (recommended): `brew install ollama && ollama pull qwen3:8b`
