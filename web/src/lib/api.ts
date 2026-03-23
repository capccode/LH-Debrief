import type { Profile, Block, OllamaModel, JobStatus, LogMessage } from "./types";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export async function fetchProfiles(): Promise<Profile[]> {
  const res = await fetch(`${API_BASE}/profiles`);
  if (!res.ok) throw new Error("Failed to fetch profiles");
  return res.json();
}

export async function fetchBlocks(): Promise<Block[]> {
  const res = await fetch(`${API_BASE}/blocks`);
  if (!res.ok) throw new Error("Failed to fetch blocks");
  return res.json();
}

export async function fetchOllamaModels(): Promise<OllamaModel[]> {
  const res = await fetch(`${API_BASE}/providers/ollama/models`);
  if (!res.ok) return [];
  return res.json();
}

export async function createJob(formData: FormData): Promise<{ job_id: string }> {
  const res = await fetch(`${API_BASE}/jobs`, {
    method: "POST",
    body: formData,
  });
  if (!res.ok) throw new Error("Failed to create job");
  return res.json();
}

export async function fetchJobStatus(jobId: string): Promise<JobStatus> {
  const res = await fetch(`${API_BASE}/jobs/${jobId}/status`);
  if (!res.ok) throw new Error("Failed to fetch job status");
  return res.json();
}

export async function fetchJobOutput(jobId: string, filename: string): Promise<string> {
  const res = await fetch(`${API_BASE}/jobs/${jobId}/output/${encodeURIComponent(filename)}`);
  if (!res.ok) throw new Error("Failed to fetch output file");
  return res.text();
}

export function connectJobLogs(
  jobId: string,
  onMessage: (msg: LogMessage) => void
): WebSocket {
  const wsBase = API_BASE.replace(/^http/, "ws");
  const ws = new WebSocket(`${wsBase}/jobs/${jobId}/logs`);
  ws.onmessage = (event) => {
    const msg: LogMessage = JSON.parse(event.data);
    onMessage(msg);
  };
  return ws;
}
