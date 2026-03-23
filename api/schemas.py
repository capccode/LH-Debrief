"""Pydantic models for API request/response shapes."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel


class HealthResponse(BaseModel):
    status: str


class ProfileInfo(BaseModel):
    id: str
    name: str
    description: str
    context: str | None = None
    blocks: list[str]


class BlockInfo(BaseModel):
    name: str
    display_name: str
    description: str
    prompt: str
    json_example: str


class OllamaModel(BaseModel):
    name: str
    size: int | None = None
    modified_at: str | None = None


class JobCreateResponse(BaseModel):
    job_id: str
    status: str


class JobStatus(BaseModel):
    job_id: str
    status: Literal["queued", "running", "completed", "failed"]
    stage: str | None = None
    progress: str | None = None
    files: list[str] = []
    error: str | None = None


class LogMessage(BaseModel):
    timestamp: str
    stage: str
    message: str
    status: Literal["running", "done", "error"]


class SettingsResponse(BaseModel):
    hf_token_set: bool
    anthropic_key_set: bool
    ollama_host: str


class SettingsUpdate(BaseModel):
    hf_token: str | None = None
    anthropic_key: str | None = None
    ollama_host: str | None = None
