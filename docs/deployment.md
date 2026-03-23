# Deployment

## Local Development

Run all three services in separate terminals:

```bash
# Terminal 1: FastAPI backend
uvicorn api.main:app --reload --port 8000

# Terminal 2: Next.js frontend
cd web && npm run dev

# Terminal 3 (optional): Open in browser
open http://localhost:3000
```

The frontend expects the API at `http://localhost:8000` by default. Override with the `NEXT_PUBLIC_API_URL` environment variable if needed.

---

## Standalone FastAPI (Tailscale / AWS)

The FastAPI backend works as a standalone API server for remote access — no frontend required.

### Tailscale

1. Install Tailscale on your server machine
2. Clone the repo and install dependencies:
   ```bash
   git clone https://github.com/capccode/LH-Debrief.git
   cd LH-Debrief
   uv sync
   ```
3. Configure `.env` with your API keys (see Environment Variables below)
4. Start the server:
   ```bash
   uvicorn api.main:app --host 0.0.0.0 --port 8000
   ```
5. Access from any Tailscale device at `http://<tailscale-ip>:8000`
6. Interactive API docs at `http://<tailscale-ip>:8000/docs`

### AWS (EC2 / ECS)

1. Set up an EC2 instance with Python 3.12+, FFmpeg, and a GPU (recommended)
2. Clone the repo and install:
   ```bash
   git clone https://github.com/capccode/LH-Debrief.git
   cd LH-Debrief
   uv sync
   ```
3. Configure `.env` or set environment variables directly
4. Run behind a reverse proxy (nginx or caddy):
   ```bash
   uvicorn api.main:app --host 127.0.0.1 --port 8000 --workers 1
   ```

!!! note
    Use `--workers 1` because the pipeline is GPU-intensive and uses an in-memory job store. Multiple workers would create separate job stores with no shared state.

---

## Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `HF_TOKEN` | Yes | — | Hugging Face token (must accept pyannote/speaker-diarization-3.1 license) |
| `ANTHROPIC_API_KEY` | For Anthropic provider | — | Claude API key |
| `OLLAMA_HOST` | No | `http://localhost:11434` | Ollama endpoint URL |

---

## Production Considerations

- **Job store**: The in-memory job store works for single-user deployments. For multi-user, you would need Redis or a database-backed store.
- **GPU**: Strongly recommended for diarization (Pyannote) and transcription (Whisper). CPU works but is significantly slower.
- **Concurrency**: The pipeline processes one job at a time — no concurrent GPU workloads. Jobs are queued and executed sequentially.
- **Security**: The API has no authentication. If exposed beyond localhost or a private network, add a reverse proxy with auth.

---

## Desktop App

For a click-to-run experience that bundles the backend automatically, see the [Desktop App](desktop.md) guide.
