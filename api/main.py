"""FastAPI backend for LH-Debrief pipeline."""

from __future__ import annotations

import asyncio
import os
import sys
from pathlib import Path

# Add src/ and api/ to path so modules resolve when run via uvicorn
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent.parent / ".env")

import httpx
from fastapi import FastAPI, File, Form, HTTPException, UploadFile, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse

from jobs import JobStore, run_pipeline, save_upload
from schemas import (
    BlockInfo,
    HealthResponse,
    JobCreateResponse,
    JobStatus,
    OllamaModel,
    ProfileInfo,
)

app = FastAPI(title="LH-Debrief API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

store = JobStore()


# --- Health ---


@app.get("/health", response_model=HealthResponse)
async def health() -> dict[str, str]:
    return {"status": "ok"}


# --- Profiles & Blocks ---


@app.get("/profiles", response_model=list[ProfileInfo])
async def get_profiles() -> list[dict]:
    from profiles import list_profiles, load_profile

    result = []
    for stem in list_profiles():
        p = load_profile(stem)
        result.append(
            {
                "id": stem,
                "name": p["name"],
                "description": p["description"],
                "context": p.get("context"),
                "blocks": p["blocks"],
            }
        )
    return result


@app.get("/blocks", response_model=list[BlockInfo])
async def get_blocks() -> list[dict]:
    from profiles import list_blocks, load_block

    result = []
    for stem in list_blocks():
        b = load_block(stem)
        result.append(
            {
                "name": b["name"],
                "display_name": b["display_name"],
                "description": b["description"],
                "prompt": b["prompt"],
                "json_example": b["json_example"],
            }
        )
    return result


# --- Ollama proxy ---


@app.get("/providers/ollama/models", response_model=list[OllamaModel])
async def get_ollama_models() -> list[dict]:
    ollama_host = os.getenv("OLLAMA_HOST", "http://localhost:11434")
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.get(f"{ollama_host}/api/tags")
            resp.raise_for_status()
            data = resp.json()
            return [
                {
                    "name": m["name"],
                    "size": m.get("size"),
                    "modified_at": m.get("modified_at"),
                }
                for m in data.get("models", [])
            ]
    except (httpx.ConnectError, httpx.TimeoutException, httpx.HTTPStatusError, OSError):
        return []


# --- Jobs ---


@app.post("/jobs", response_model=JobCreateResponse)
async def create_job(
    file: UploadFile = File(...),
    profile: str | None = Form(None),
    blocks: str | None = Form(None),
    add_blocks: str | None = Form(None),
    provider: str = Form("anthropic"),
    model: str | None = Form(None),
    context: str | None = Form(None),
    output_dir: str | None = Form(None),
) -> dict[str, str]:
    # Parse comma-separated lists
    blocks_list = [b.strip() for b in blocks.split(",") if b.strip()] if blocks else None
    add_blocks_list = (
        [b.strip() for b in add_blocks.split(",") if b.strip()] if add_blocks else None
    )

    # Validation
    if blocks_list and profile:
        raise HTTPException(400, "profile and blocks are mutually exclusive")
    if add_blocks_list and not profile:
        raise HTTPException(400, "add_blocks requires a profile")
    if provider not in ("anthropic", "ollama"):
        raise HTTPException(400, f"unknown provider: {provider}")

    # Save uploaded file
    filename, upload_dir = await save_upload(file)

    job_id = await store.create_job(
        upload_filename=filename,
        upload_dir=upload_dir,
        profile=profile,
        blocks=blocks_list,
        add_blocks=add_blocks_list,
        provider=provider,
        model=model,
        context=context,
        output_dir=output_dir,
    )

    asyncio.create_task(run_pipeline(job_id, store))

    return {"job_id": job_id, "status": "queued"}


@app.get("/jobs/{job_id}/status", response_model=JobStatus)
async def get_job_status(job_id: str) -> dict:
    job = await store.get_job(job_id)
    if not job:
        raise HTTPException(404, f"job {job_id} not found")
    return {
        "job_id": job.job_id,
        "status": job.status,
        "stage": job.stage,
        "progress": job.progress,
        "files": job.files,
        "error": job.error,
    }


@app.get("/jobs/{job_id}/output/{filename}")
async def get_job_output(job_id: str, filename: str) -> FileResponse:
    job = await store.get_job(job_id)
    if not job:
        raise HTTPException(404, f"job {job_id} not found")
    if not job.output_dir:
        raise HTTPException(404, "no output directory for this job")

    file_path = job.output_dir / filename
    if not file_path.exists() or not file_path.is_file():
        raise HTTPException(404, f"file {filename} not found")

    # Path traversal protection
    if not file_path.resolve().is_relative_to(job.output_dir.resolve()):
        raise HTTPException(403, "access denied")

    # Content type detection
    suffix = file_path.suffix.lower()
    media_types = {
        ".md": "text/markdown",
        ".json": "application/json",
        ".txt": "text/plain",
    }
    media_type = media_types.get(suffix, "application/octet-stream")

    return FileResponse(file_path, media_type=media_type)


# --- WebSocket for live logs ---


@app.websocket("/jobs/{job_id}/logs")
async def job_logs_ws(websocket: WebSocket, job_id: str) -> None:
    job = await store.get_job(job_id)
    if not job:
        await websocket.close(code=4004, reason="job not found")
        return

    await websocket.accept()
    offset = 0

    try:
        while True:
            logs = await store.get_logs(job_id, offset=offset)
            for log_msg in logs:
                await websocket.send_json(log_msg.model_dump())
            offset += len(logs)

            # Check if job has reached terminal state
            job = await store.get_job(job_id)
            if job and job.status in ("completed", "failed"):
                # Flush any remaining logs
                final_logs = await store.get_logs(job_id, offset=offset)
                for log_msg in final_logs:
                    await websocket.send_json(log_msg.model_dump())
                await websocket.close(code=1000)
                break

            await asyncio.sleep(0.3)
    except WebSocketDisconnect:
        pass
