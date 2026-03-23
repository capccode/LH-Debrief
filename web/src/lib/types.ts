export interface Profile {
  id: string;
  name: string;
  description: string;
  context: string;
  blocks: string[];
}

export interface Block {
  name: string;
  display_name: string;
  description: string;
  prompt: string;
  json_example: string;
}

export interface OllamaModel {
  name: string;
  size: number;
  modified: string;
}

export interface JobStatus {
  job_id: string;
  status: "queued" | "processing" | "completed" | "failed";
  stage: string;
  progress: string;
  files: string[];
  error: string | null;
}

export interface LogMessage {
  timestamp: string;
  stage: string;
  message: string;
  status: "running" | "done" | "error";
}
